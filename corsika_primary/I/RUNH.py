import struct

MARKER_FLOAT32 = struct.unpack("f", "RUNH".encode())[0]

MARKER = 1 - 1
RUN_NUMBER = 2 - 1
NUM_EVENTS = 93 - 1
