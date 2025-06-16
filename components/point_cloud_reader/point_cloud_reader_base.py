"""This module contains a base class for reading point clouds."""
from abc import ABC
from abc import abstractmethod
from pathlib import Path

import numpy as np


class PotreePointCloudReaderBase(ABC):
    """Base class for reading point clouds in Potree format."""

    TYPES_MAPPING = {
        "uint8": np.uint8,
        "uint16": np.uint16,
        "uint32": np.uint32,
        "int16": np.int16,
        "float": np.float32,
        "double": np.float64
    }

    def __init__(self):
        """Creates an instance of the class."""
        self._metadata = None

    @abstractmethod
    def read_point_cloud(self, path: Path) -> np.ndarray:
        """Reads a point cloud from the provided path.

        Args:
            path: A path to file(s) to read.

        Returns:
            Point cloud as a numpy array.
        """
        ...
