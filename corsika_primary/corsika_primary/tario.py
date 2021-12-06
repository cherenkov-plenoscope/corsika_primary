import tarfile
import numpy as np
from . import I

RUNH_FILENAME = "runh.float32"
EVTH_FILENAME = "{:09d}.evth.float32"
BUNCHES_FILENAME = "{:09d}.cherenkov_bunches.Nx8_float32"


class Tario:
    def __init__(self, path):
        self.path = path
        self.tar = tarfile.open(path, "r|*")

        runh_tar = self.tar.next()
        runh_bin = self.tar.extractfile(runh_tar).read()
        self.runh = np.frombuffer(runh_bin, dtype=np.float32)
        assert self.runh[0] == I.RUNH.MARKER_FLOAT32
        self.num_events_read = 0

    def __next__(self):
        evth_tar = self.tar.next()
        if evth_tar is None:
            raise StopIteration
        evth_number = int(evth_tar.name[0:9])
        evth_bin = self.tar.extractfile(evth_tar).read()
        evth = np.frombuffer(evth_bin, dtype=np.float32)
        assert evth[0] == I.EVTH.MARKER_FLOAT32
        assert int(np.round(evth[1])) == evth_number

        bunches_tar = self.tar.next()
        bunches_number = int(bunches_tar.name[0:9])
        assert evth_number == bunches_number
        bunches_bin = self.tar.extractfile(bunches_tar).read()
        bunches = np.frombuffer(bunches_bin, dtype=np.float32)
        num_bunches = bunches.shape[0] // (8)

        self.num_events_read += 1
        return (evth, np.reshape(bunches, newshape=(num_bunches, 8)))

    def __iter__(self):
        return self

    def __exit__(self):
        self.tar.close()

    def __repr__(self):
        out = "{:s}(path='{:s}', read={:d})".format(
            self.__class__.__name__, self.path, self.num_events_read
        )
        return out
