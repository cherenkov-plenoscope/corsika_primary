import struct

MARKER_FLOAT32 = struct.unpack("f", "EVTE".encode())[0]
MARKER = 1 - 1
