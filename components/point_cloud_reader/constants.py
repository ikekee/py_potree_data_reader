"""This module contains constant values for point cloud reader."""
# Potree 2.0 file format filenames
HIERARCHY_BINARY_FILENAME = 'hierarchy.bin'
OCTREE_BINARY_FILENAME = 'octree.bin'
METADATA_FILENAME = 'metadata.json'

# Potree data format constants
MIN_BYTES_FOR_MORTON_CODE = 16
BYTES_FOR_RGB = 8
BYTES_PER_NODE = 22
POTREE_PROXY_NODE_TYPE = 2
NUM_POINTS_BEGIN_BYTE = 2
NUM_POINTS_END_BYTE = 6

# Potree metadata keys
ENCODING_KEY = 'encoding'
VERSION_KEY = 'version'
POINTS_KEY = 'points'
SCALE_KEY = 'scale'
OFFSET_KEY = 'offset'
ATTRIBUTES_KEY = "attributes"
# Potree metadata attributes keys
ATTRIBUTE_NAME_KEY = "name"
ATTRIBUTE_TYPE_KEY = "type"
ATTRIBUTE_SIZE_KEY = "size"

# Potree metadata attributes types
POSITION_ATTRIBUTE = "position"
RGBA_ATTRIBUTE = "rgba"
