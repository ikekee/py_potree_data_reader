"""This module contains a class for reading uncompressed Potree point clouds."""
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List

import numpy as np

from components.common.files_lib import open_json
from components.point_cloud_reader.point_cloud_reader_base import PotreePointCloudReaderBase


def calculate_bytes_per_point(attributes: List[Dict[str, Any]]) -> int:
    """Calculates the number of bytes per one point using Potree attributes data.

    It is calculated as the sum of attributes' sizes.

    Args:
        attributes: Potree point cloud attributes data.

    Returns:
        The number of bytes per point.
    """
    bytes_per_point = 0
    for attribute in attributes:
        bytes_per_point += attribute["size"]
    return bytes_per_point


class PotreeUncompressedPointCloudReader(PotreePointCloudReaderBase):
    """This class encapsulates the functionality to read uncompressed Potree format data.

    Attributes:
        POTREE_FORMAT_VERSION: Potree data format version.
    """

    POTREE_FORMAT_VERSION = "2.0"
    POTREE_DATA_ENCODING = "DEFAULT"

    def _check_potree_format_version(self, metadata: Dict[str, Any]):
        """Checks whether the Potree data format version is supported. Raises an exception if not.

        Args:
            metadata: Potree data format metadata.
        """
        if metadata["version"] != self.POTREE_FORMAT_VERSION:
            raise ValueError(f"Potree format version {metadata['version']} is not supported")

    def _check_potree_data_encoding(self, metadata: Dict[str, Any]):
        """Checks whether the Potree data encoding is supported. Raises an exception if not.

        Args:
            metadata: Potree data format metadata.
        """
        if metadata["encoding"] != self.POTREE_DATA_ENCODING:
            raise ValueError(f"Potree data encoding {metadata['encoding']} is not supported")

    def read_point_cloud(self, path: Path) -> np.ndarray:
        """Reads the point cloud from the given path.

        Args:
            path: Path to the folder with the Potree files.

        Returns:
            Numpy array with the read point cloud.
        """
        metadata = open_json(path / "metadata.json")
        self._check_potree_format_version(metadata)
        num_points = metadata["points"]
        offset = metadata["offset"]
        scale = metadata["scale"]
        bytes_per_point = calculate_bytes_per_point(metadata["attributes"])
        points = []
        with open(path / "octree.bin", 'rb') as file:
            for _ in range(num_points):
                point_coordinates = np.frombuffer(file.read(12), dtype=np.int32)
                source_point_coordinates = point_coordinates * scale + offset
                points.append(source_point_coordinates)
                file.seek(bytes_per_point - 12, 1)
        return np.array(points)
