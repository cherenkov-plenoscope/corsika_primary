import struct

MARKER_FLOAT32 = struct.unpack("f", "RUNE".encode())[0]

MARKER = 1 - 1
