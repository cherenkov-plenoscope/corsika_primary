import tarfile
import numpy as np
import re as regex
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
        self.tar = tarfile.open(name=path, mode="r|")

        self.next_info = self.tar.next()
        self.readme = read_readme(tar=self.tar, tarinfo=self.next_info)

        self.next_info = self.tar.next()
        self.runh = read_runh(tar=self.tar, tarinfo=self.next_info)
        self.rune = None
        self.run_number = int(self.runh[I.RUNH.RUN_NUMBER])

        self.next_info = self.tar.next()

    def __next__(self):
        if self.next_info is None:
            raise StopIteration
        if not is_evth_path(self.next_info.name):
            self.rune = read_rune(
                tar=self.tar,
                tarinfo=self.next_info,
                run_number=self.run_number,
            )
            self.next_info = self.tar.next()
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
        self.evte = None

    def __next__(self):
        if self.run.next_info is None:
            raise StopIteration
        if not is_cherenkov_block_path(self.run.next_info.name):
            self.evte = read_evte(
                tar=self.run.tar,
                tarinfo=self.run.next_info,
                run_number=self.run.run_number,
                event_number=self.run.event_number,
            )
            self.run.next_info = self.run.tar.next()
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


def is_match(template, path):
    """
    Returns true if a path matches a template, false if not.

    parameters
    ----------
    template : str
        A template defining match.
    path : str
        The path to be tested for matching.
    """
    digit_format_regex = regex.compile(r"\{\w{0,100}:09d\}")
    ss = digit_format_regex.split(template)
    math = (9 * "#").join(ss)
    if len(math) != len(path):
        return False
    for i in range(len(math)):
        t = math[i]
        p = path[i]
        if t == "#":
            if not str.isdigit(p):
                return False
        else:
            if t != p:
                return False
    return True


VERSION_FILENAME = "{run_number:09d}/version.txt"
RUNH_FILENAME = "{run_number:09d}/RUNH.float32"
EVTH_FILENAME = "{run_number:09d}/{event_number:09d}/EVTH.float32"
CHERENKOV_BLOCK_FILENAME = "{run_number:09d}/{event_number:09d}/{cherenkov_block_number:09d}.cer.x8.float32"
EVTE_FILENAME = "{run_number:09d}/{event_number:09d}/EVTE.float32"
RUNE_FILENAME = "{run_number:09d}/RUNE.float32"


def is_cherenkov_block_path(path):
    return is_match(CHERENKOV_BLOCK_FILENAME, path)


def is_evth_path(path):
    return is_match(EVTH_FILENAME, path)


def is_evte_path(path):
    return is_match(EVTE_FILENAME, path)


def is_runh_path(path):
    return is_match(RUNH_FILENAME, path)


def is_rune_path(path):
    return is_match(RUNE_FILENAME, path)


def parse_run_number(path):
    return int(path[0 : 0 + 9])


def parse_event_number(path):
    return int(path[10 : 10 + 9])


def parse_cherenkov_block_number(path):
    return int(path[20 : 20 + 9])


def read_readme(tar, tarinfo):
    assert is_match(VERSION_FILENAME, tarinfo.name)
    readme_bin = tar.extractfile(tarinfo).read()
    return readme_bin.decode("ascii")


def read_runh(tar, tarinfo):
    assert is_runh_path(tarinfo.name)
    runh_bin = tar.extractfile(tarinfo).read()
    runh = np.frombuffer(runh_bin, dtype=np.float32)
    assert runh.shape[0] == 273
    assert runh[I.RUNH.MARKER] == I.RUNH.MARKER_FLOAT32
    assert runh[I.RUNH.RUN_NUMBER] == parse_run_number(tarinfo.name)
    return runh


def read_rune(tar, tarinfo, run_number):
    assert is_rune_path(tarinfo.name)
    assert parse_run_number(tarinfo.name) == run_number
    rune_bin = tar.extractfile(tarinfo).read()
    rune = np.frombuffer(rune_bin, dtype=np.float32)
    assert rune.shape[0] == 273
    assert rune[I.RUNE.MARKER] == I.RUNE.MARKER_FLOAT32
    return rune


def read_evth(tar, tarinfo):
    assert is_evth_path(tarinfo.name)
    event_number_path = parse_event_number(tarinfo.name)
    evth_bin = tar.extractfile(tarinfo).read()
    evth = np.frombuffer(evth_bin, dtype=np.float32)
    assert evth.shape[0] == 273
    assert evth[I.EVTH.MARKER] == I.EVTH.MARKER_FLOAT32
    assert evth[I.EVTH.RUN_NUMBER] == parse_run_number(tarinfo.name)
    assert evth[I.EVTH.EVENT_NUMBER] == parse_event_number(tarinfo.name)
    return evth


def read_evte(tar, tarinfo, run_number, event_number):
    assert is_evte_path(tarinfo.name)
    assert parse_run_number(tarinfo.name) == run_number
    assert parse_event_number(tarinfo.name) == event_number
    evte_bin = tar.extractfile(tarinfo).read()
    evte = np.frombuffer(evte_bin, dtype=np.float32)
    assert evte.shape[0] == 273
    assert evte[I.EVTE.MARKER] == I.EVTE.MARKER_FLOAT32
    return evte


def read_cherenkov_bunch_block(tar, tarinfo):
    assert is_cherenkov_block_path(tarinfo.name)
    bunches_bin = tar.extractfile(tarinfo).read()
    bunches = np.frombuffer(bunches_bin, dtype=np.float32)
    num_bunches = bunches.shape[0] // (8)
    return np.reshape(bunches, newshape=(num_bunches, 8))
