"""This module contains a class for reading Potree point cloud compressed with Brotli."""
from collections import defaultdict
from pathlib import Path
import struct
from typing import Dict
from typing import List
from typing import Optional

import brotli
import numpy as np

from components.common.files_lib import open_json
from components.point_cloud_reader.constants import ATTRIBUTE_MIN_KEY
from components.point_cloud_reader.constants import ATTRIBUTE_NAME_KEY
from components.point_cloud_reader.constants import ATTRIBUTE_SIZE_KEY
from components.point_cloud_reader.constants import ATTRIBUTE_TYPE_KEY
from components.point_cloud_reader.constants import ATTRIBUTES_KEY
from components.point_cloud_reader.constants import BYTES_FOR_RGB
from components.point_cloud_reader.constants import BYTES_PER_NODE
from components.point_cloud_reader.constants import CUSTOM_ID_ATTRIBUTE
from components.point_cloud_reader.constants import ENCODING_KEY
from components.point_cloud_reader.constants import HIERARCHY_BINARY_FILENAME
from components.point_cloud_reader.constants import METADATA_FILENAME
from components.point_cloud_reader.constants import MIN_BYTES_FOR_MORTON_CODE
from components.point_cloud_reader.constants import NUM_POINTS_BEGIN_BYTE
from components.point_cloud_reader.constants import NUM_POINTS_END_BYTE
from components.point_cloud_reader.constants import OCTREE_BINARY_FILENAME
from components.point_cloud_reader.constants import OFFSET_KEY
from components.point_cloud_reader.constants import POINTS_KEY
from components.point_cloud_reader.constants import POSITION_ATTRIBUTE
from components.point_cloud_reader.constants import POTREE_PROXY_NODE_TYPE
from components.point_cloud_reader.constants import RGB_ATTRIBUTE
from components.point_cloud_reader.constants import SCALE_KEY
from components.point_cloud_reader.constants import VERSION_KEY
from components.point_cloud_reader.point_cloud_reader_base import PotreePointCloudReaderBase


def dealign24b(morton_code: int):
    """Removes odd bits from provided value.

    This code is adapted from
    https://github.com/potree/potree/blob/develop/src/modules/loader/2.0/DecoderWorker_brotli.js.

    Args:
        morton_code: Integer value from the morton code to be dealigned.

    Returns:
        Value with odd bits removed.
    """
    x = morton_code
    x = ((x & 0b001000001000001000001000) >> 2) | ((x & 0b000001000001000001000001) >> 0)
    x = ((x & 0b000011000000000011000000) >> 4) | ((x & 0b000000000011000000000011) >> 0)
    x = ((x & 0b000000001111000000000000) >> 8) | ((x & 0b000000000000000000001111) >> 0)
    x = ((x & 0b000000000000000000000000) >> 16) | ((x & 0b000000000000000011111111) >> 0)
    return x


def read_node_positions_data(morton_code_bytes: bytes, num_points: int) -> Optional[np.ndarray]:
    """Reads points positions from octree node.

    Args:
        morton_code_bytes: Bytes containing positions data in morton code.
        num_points: Number of points in the node.

    Returns:
        Numpy array of points' positions if node is valid, otherwise None.
    """
    if len(morton_code_bytes) < MIN_BYTES_FOR_MORTON_CODE:
        return None
    dt = np.dtype(np.uint32).newbyteorder('<')
    morton_data = np.frombuffer(morton_code_bytes, dtype=dt, count=num_points * 4).reshape((-1, 4))

    mc_1, mc_0, mc_3, mc_2 = [*morton_data.T]
    x = dealign24b((mc_3 & 0x00FFFFFF) >> 0) | (dealign24b(((mc_3 >> 24) | (mc_2 << 8)) >> 0) << 8)
    y = dealign24b((mc_3 & 0x00FFFFFF) >> 1) | (dealign24b(((mc_3 >> 24) | (mc_2 << 8)) >> 1) << 8)
    z = dealign24b((mc_3 & 0x00FFFFFF) >> 2) | (dealign24b(((mc_3 >> 24) | (mc_2 << 8)) >> 2) << 8)
    if np.any(mc_1 != 0) or np.any(mc_2 != 0):
        x |= ((dealign24b((mc_1 & 0x00FFFFFF) >> 0) << 16) |
              (dealign24b(((mc_1 >> 24) | (mc_0 << 8)) >> 0) << 24))
        y |= ((dealign24b((mc_1 & 0x00FFFFFF) >> 1) << 16) |
              (dealign24b(((mc_1 >> 24) | (mc_0 << 8)) >> 1) << 24))
        z |= ((dealign24b((mc_1 & 0x00FFFFFF) >> 2) << 16) |
              (dealign24b(((mc_1 >> 24) | (mc_0 << 8)) >> 2) << 24))
    return np.column_stack((x, y, z))


def read_node_rgb_data(morton_code_bytes: bytes, num_points: int) -> Optional[np.ndarray]:
    """Reads points RGB data from octree node.

    Args:
        morton_code_bytes: Bytes containing points data in morton code.
        num_points: Number of points in the node.

    Returns:
        Numpy array of points' colors data.
    """
    dt = np.dtype(np.uint32).newbyteorder('<')
    morton_data = np.frombuffer(morton_code_bytes, dtype=dt, count=num_points * 2).reshape((-1, 2))
    mc_1, mc_0 = [*morton_data.T]
    r = dealign24b((mc_1 & 0x00FFFFFF) >> 0) | (dealign24b(((mc_1 >> 24) | (mc_0 << 8)) >> 0) << 8)
    g = dealign24b((mc_1 & 0x00FFFFFF) >> 1) | (dealign24b(((mc_1 >> 24) | (mc_0 << 8)) >> 1) << 8)
    b = dealign24b((mc_1 & 0x00FFFFFF) >> 2) | (dealign24b(((mc_1 >> 24) | (mc_0 << 8)) >> 2) << 8)
    r = np.where(r > 255, r/256, r)
    g = np.where(g > 255, g/256, g)
    b = np.where(b > 255, b/256, b)
    return np.column_stack((r, g, b))


def parse_potree_hierarchy(hierarchy_bytes: bytes) -> List[List[int]]:
    """Parses the bytes from the Potree hierarchy file.

    Args:
        hierarchy_bytes: Bytes containing Potree nodes data.

    Returns:
        A numpy array with data for each Potree node.
    """
    data_to_read = []
    for begin_index in range(0, len(hierarchy_bytes), BYTES_PER_NODE):
        node_type = hierarchy_bytes[begin_index]
        num_points_bytes = hierarchy_bytes[
                           begin_index + NUM_POINTS_BEGIN_BYTE:begin_index + NUM_POINTS_END_BYTE]
        num_points = struct.unpack("i", num_points_bytes)[0]
        byte_offset, byte_size = struct.unpack(
            "qq",
            hierarchy_bytes[begin_index + NUM_POINTS_END_BYTE:begin_index + BYTES_PER_NODE]
        )
        # Skipping proxy nodes (https://github.com/potree/potree/blob/c53cf7f7e692ee27bc4c2c623fe17bd678d25558/src/modules/loader/2.0/OctreeLoader.js#L179)
        # and nodes with zero bytes size (check line 196) in link above
        if node_type != POTREE_PROXY_NODE_TYPE and byte_size != 0:
            data_to_read.append([num_points, byte_offset, byte_size])
    return data_to_read


class PotreeBrotliCompressedPointCloudReader(PotreePointCloudReaderBase):
    """This class encapsulates the functionality to read uncompressed Potree format data.

    Attributes:
        POTREE_FORMAT_VERSION: Potree data format version.
        POTREE_DATA_ENCODING: Potree data encoding type.
        _metadata: Potree data metadata dictionary.
    """

    POTREE_FORMAT_VERSION = "2.0"
    POTREE_DATA_ENCODING = "BROTLI"

    def __init__(self):
        """Creates an instance of the class."""
        super().__init__()

    def _check_potree_format_version(self):
        """Checks and raises an exception if Potree data format version is not supported."""
        if self._metadata[VERSION_KEY] != self.POTREE_FORMAT_VERSION:
            raise ValueError(
                f"Potree format version {self._metadata[VERSION_KEY]} is not supported")

    def _check_potree_data_encoding(self):
        """Checks whether the Potree data encoding is supported. Raises an exception if not."""
        if self._metadata[ENCODING_KEY] != self.POTREE_DATA_ENCODING:
            raise ValueError(
                f"Potree data encoding {self._metadata[ENCODING_KEY]} is not supported"
            )

    def _read_potree_octree(self,
                            data_to_read: List[List[int]],
                            octree_bytes: bytes) -> Dict[str, np.ndarray]:
        """Reads points from the given octree data.

        Args:
            data_to_read: A list with data for reading octree nodes.
            octree_bytes: Bytes containing octree data.

        Returns:
            A numpy array with points from all nodes in the octree.
        """
        data = defaultdict(lambda: np.zeros(self._metadata[POINTS_KEY]))
        current_index = 0
        for num_points, byte_offset, byte_size in data_to_read:
            brotli_compressed_node_bytes = octree_bytes[byte_offset: byte_offset + byte_size]
            node_bytes = brotli.decompress(brotli_compressed_node_bytes)
            attributes_byte_offset = 0
            for attribute_metadata in self._metadata[ATTRIBUTES_KEY]:
                if attribute_metadata[ATTRIBUTE_NAME_KEY] == POSITION_ATTRIBUTE:
                    positions = read_node_positions_data(node_bytes, num_points)
                    read_bytes_num = num_points * MIN_BYTES_FOR_MORTON_CODE
                    data[POSITION_ATTRIBUTE][current_index: current_index + num_points] = positions
                elif attribute_metadata[ATTRIBUTE_NAME_KEY] == RGB_ATTRIBUTE:
                    colors = read_node_rgb_data(node_bytes, num_points)
                    read_bytes_num = num_points * BYTES_FOR_RGB
                    data[RGB_ATTRIBUTE][current_index: current_index + num_points] = colors
                else:
                    attribute_name = attribute_metadata[ATTRIBUTE_NAME_KEY]
                    numpy_dtype = self.TYPES_MAPPING[attribute_name]
                    dt = np.dtype(numpy_dtype).newbyteorder('<')
                    read_bytes_num = attribute_metadata[ATTRIBUTE_SIZE_KEY] * num_points
                    bytes_to_read = node_bytes[
                                    attributes_byte_offset: attributes_byte_offset + read_bytes_num]
                    attribute_data = np.frombuffer(bytes_to_read, dtype=dt)
                    data[attribute_name][current_index: current_index + num_points] = attribute_data
                attributes_byte_offset += read_bytes_num
                current_index += num_points
        return data

    def read_point_cloud(self, path: Path) -> np.ndarray:
        """Reads the point cloud from the given path.

        Args:
            path: Path to the folder with the Potree files.

        Returns:
            Numpy array with the read point cloud.
        """
        self._metadata = open_json(path / METADATA_FILENAME)
        self._check_potree_format_version()
        self._check_potree_data_encoding()

        with open(path / HIERARCHY_BINARY_FILENAME, "rb") as hierarchy_file:
            hierarchy_bytes = hierarchy_file.read()

        with open(path / OCTREE_BINARY_FILENAME, "rb") as octree_file:
            octree_bytes = octree_file.read()

        data_to_read = parse_potree_hierarchy(hierarchy_bytes)

        points = self._read_potree_octree(data_to_read, octree_bytes)
        if len(points) != self._metadata[POINTS_KEY]:
            raise ValueError(
                f"Points number mismatch: {len(points)} vs {self._metadata[POINTS_KEY]}")

        scale = np.array(self._metadata[SCALE_KEY], dtype=np.float32)
        offset = np.array(self._metadata[OFFSET_KEY], dtype=np.float64)
        return points * scale + offset
