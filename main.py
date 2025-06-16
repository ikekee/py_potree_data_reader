from argparse import ArgumentParser
from pathlib import Path

import numpy as np

from components.common.files_lib import create_path_if_not_exists
from components.point_cloud_reader.potree_brotli_compressed_pc_reader import (
    PotreeBrotliCompressedPointCloudReader,
)


def main(input_path: Path, output_path: Path):
    reader = PotreeBrotliCompressedPointCloudReader()
    data = reader.read_point_cloud(input_path)
    for attribute_name in data.keys():
        data[attribute_name] = np.expand_dims(data[attribute_name], axis=1) if data[attribute_name].ndim == 1 else data[attribute_name]
    create_path_if_not_exists(output_path)
    data_for_saving = np.hstack(list(data.values()))
    np.savetxt(output_path/"points.txt", data_for_saving, header=",".join(data.keys()), delimiter=",")
    

if __name__ == '__main__':
    argparse = ArgumentParser()
    argparse.add_argument(
        "-p",
        "--path",
        help="Path to potree point cloud for reading.",
        required=True,
        type=Path
    )
    argparse.add_argument(
        "-o",
        "--output",
        help="Path to save output point cloud.",
        required=True,
        type=Path
    )
    args = argparse.parse_args()
    main(args.path, args.output)
