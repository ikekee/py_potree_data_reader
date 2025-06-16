"""This module contains a functions for point cloud reading functionalities."""
from common.configuration import ScenePointCloudReaderConfiguration
from components.point_cloud_reader.point_cloud_reader_base import PotreePointCloudReaderBase
from components.point_cloud_reader.point_cloud_reader_type import PointCloudReaderType
from components.point_cloud_reader.potree_brotli_compressed_pc_reader import (
    PotreeBrotliCompressedPointCloudReader,
)
from components.point_cloud_reader.potree_uncompressed_pc_reader import (
    PotreeUncompressedPointCloudReader,
)


def create_point_cloud_reader(config: ScenePointCloudReaderConfiguration) -> PotreePointCloudReaderBase:
    """Creates an instance of a point cloud reader according to the configuration.

    Args:
        config: ScenePointCloudReaderConfiguration instance.

    Returns:
        An instance of the class implementing the point cloud reader.
    """
    reader_name = config.reader_name
    if reader_name == PointCloudReaderType.POTREE_UNCOMPRESSED_POINT_CLOUD_READER.value:
        pc_reader = PotreeUncompressedPointCloudReader()
    elif reader_name == PointCloudReaderType.POTREE_BROTLI_COMPRESSED_POINT_CLOUD_READER.value:
        pc_reader = PotreeBrotliCompressedPointCloudReader()
    else:
        raise ValueError(f"Unknown point cloud reader: {reader_name}")
    return pc_reader
