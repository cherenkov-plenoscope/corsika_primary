import struct

MARKER_FLOAT32 = struct.unpack("f", "RUNH".encode())[0]

NUM_EVENTS = 93 - 1