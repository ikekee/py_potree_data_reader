"""This module contains a class to represent a type of point cloud reader."""
from enum import Enum


class PointCloudReaderType(Enum):
    """A class to represent a type of point cloud reader."""

    POTREE_UNCOMPRESSED_POINT_CLOUD_READER = "potree_uncompressed_point_cloud_reader"
    POTREE_BROTLI_COMPRESSED_POINT_CLOUD_READER = "potree_brotli_compressed_point_cloud_reader"
