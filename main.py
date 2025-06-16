from argparse import ArgumentParser
from pathlib import Path


def main():
    ...


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
