import tarfile
import numpy as np
from . import I


class EventTapeReader:
    def __init__(self, path, read_block_by_block=False):
        """
        Read an event-tape written by the CORSIKA-primary-mod.

        parameters
        ----------
        path : str
            Path to the event-tape written by the CORSIKA-primary-mod.
        read_block_by_block : bool (False)
            If false, all Cherenkov-bunches of an event are read at once and
            returned by (evth, bunches) = next(self).
            If true, next(self) returns (evth, class BunchTapeReader).
            BunchTapeReader can then read Cherenkov-bunches block-by-block.
        """
        self.path = str(path)
        self.read_block_by_block = bool(read_block_by_block)
        self.tar = tarfile.open(path, "r")

        self.next_info = self.tar.next()
        self.readme = read_readme(tar=self.tar, tarinfo=self.next_info)

        self.next_info = self.tar.next()
        self.runh = read_runh(tar=self.tar, tarinfo=self.next_info)

        self.next_info = self.tar.next()

    def __next__(self):
        if self.next_info is None:
            raise StopIteration
        evth = read_evth(tar=self.tar, tarinfo=self.next_info)
        self.event_number = int(evth[I.EVTH.EVENT_NUMBER])

        self.next_info = self.tar.next()

        if self.read_block_by_block:
            return (evth, BunchTapeReader(run=self))
        else:
            cherenkov_blocks = []
            for cherenkov_block in BunchTapeReader(run=self):
                cherenkov_blocks.append(cherenkov_block)
            return (evth, np.vstack(cherenkov_blocks))

    def __iter__(self):
        return self

    def __exit__(self):
        self.tar.close()

    def __repr__(self):
        out = "{:s}(path='{:s}')".format(self.__class__.__name__, self.path)
        return out


class BunchTapeReader:
    def __init__(self, run):
        self.run = run
        self.cherenkov_block_number = 1

    def __next__(self):
        if self.run.next_info is None:
            raise StopIteration
        if not is_cherenkov_block_path(self.run.next_info.name):
            raise StopIteration

        assert self.run.event_number == parse_event_number(
            path=self.run.next_info.name
        )
        assert self.cherenkov_block_number == parse_cherenkov_block_number(
            path=self.run.next_info.name
        )
        bunch_block = read_cherenkov_bunch_block(
            tar=self.run.tar, tarinfo=self.run.next_info,
        )
        self.cherenkov_block_number += 1
        self.run.next_info = self.run.tar.next()
        return bunch_block

    def __iter__(self):
        return self

    def __exit__(self):
        pass

    def __repr__(self):
        out = "{:s}(run.path='{:s}')".format(
            self.__class__.__name__, self.run.path
        )
        return out


def is_match(template, path, digit_wildcard="#"):
    """
    Returns true if a path matches a template, false if not.

    parameters
    ----------
    template : str
        A template defining match.
    path : str
        The path to be tested for matching.
    digit_wildcard : char
        Chars that match the wildcard are considered to be digits in 'path'
    """
    if len(template) != len(path):
        return False
    for i in range(len(template)):
        t = template[i]
        p = path[i]
        if t == digit_wildcard:
            if not str.isdigit(p):
                return False
        else:
            if t != p:
                return False
    return True


def is_cherenkov_block_path(path):
    return is_match(
        template="events/#########/cherenkov_bunches/#########.x8.float32",
        path=path,
    )


def is_evth_path(path):
    return is_match(template="events/#########/EVTH.float32", path=path,)


def parse_event_number(path):
    return int(path[7 : 7 + 9])


def parse_cherenkov_block_number(path):
    return int(path[35 : 35 + 9])


def read_readme(tar, tarinfo):
    assert tarinfo.name == "readme/version.txt"
    readme_bin = tar.extractfile(tarinfo).read()
    return readme_bin.decode("ascii")


def read_runh(tar, tarinfo):
    assert tarinfo.name == "RUNH.float32"
    runh_bin = tar.extractfile(tarinfo).read()
    runh = np.frombuffer(runh_bin, dtype=np.float32)
    assert runh.shape[0] == 273
    assert runh[I.RUNH.MARKER] == I.RUNH.MARKER_FLOAT32
    return runh


def read_evth(tar, tarinfo):
    assert is_evth_path(tarinfo.name)
    evth_bin = tar.extractfile(tarinfo).read()
    evth = np.frombuffer(evth_bin, dtype=np.float32)
    assert evth.shape[0] == 273
    assert evth[I.EVTH.MARKER] == I.EVTH.MARKER_FLOAT32
    assert evth[I.EVTH.EVENT_NUMBER] == parse_event_number(tarinfo.name)
    return evth


def read_cherenkov_bunch_block(tar, tarinfo):
    assert is_cherenkov_block_path(tarinfo.name)
    bunches_bin = tar.extractfile(tarinfo).read()
    bunches = np.frombuffer(bunches_bin, dtype=np.float32)
    num_bunches = bunches.shape[0] // (8)
    return np.reshape(bunches, newshape=(num_bunches, 8))
