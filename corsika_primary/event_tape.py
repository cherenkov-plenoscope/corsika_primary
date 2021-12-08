import tarfile
import numpy as np
import io
import re as regex
from . import I

NUM_CHERENKOV_BUNCHES_IN_BUFFER = 1048576


class EventTapeWriter:
    def __init__(self, path, buffer_capacity=NUM_CHERENKOV_BUNCHES_IN_BUFFER):
        self.path = str(path)
        self.tar = tarfile.open(name=self.path, mode="w|")
        self.run_number = None
        self.event_number = None
        self.cherenkov_block_number = None

        self.buffer = np.zeros(
            shape=(buffer_capacity, 8),
            dtype=np.float32,
        )
        self.buffer_size = 0

    def runh(self, runh):
        self.run_number = int(runh[I.RUNH.RUN_NUMBER])
        assert self.run_number > 0
        write_runh(tar=self.tar, runh=runh, run_number=self.run_number)

    def evth(self, evth):
        assert self.run_number is not None, "Expected RUNH before EVTH."
        assert self.event_number is None
        self.event_number = int(evth[I.EVTH.EVENT_NUMBER])
        self.cherenkov_block_number = 1
        write_evth(
            tar=self.tar,
            evth=evth,
            run_number=self.run_number,
            event_number=self.event_number
        )

    def bunches(self, bunches):
        assert self.event_number is not None, "Expected EVTH before bunches."
        assert bunches.dtype == np.float32
        assert bunches.shape[1] == 8
        bunches_remaining = bunches.shape[0]

        bunches_at = 0
        while bunches_remaining != 0:
            buffer_remaining = self.buffer.shape[0] - self.buffer_size
            num_to_buffer = min([buffer_remaining, bunches_remaining])

            start_buffer = self.buffer_size
            stop_buffer = start_buffer + num_to_buffer
            start_bunches = bunches_at
            stop_bunches = start_bunches + num_to_buffer

            self.buffer[start_buffer:stop_buffer, :] = bunches[start_bunches:stop_bunches, :]

            bunches_remaining -= num_to_buffer
            bunches_at = stop_bunches
            self.buffer_size = stop_buffer

            if self.buffer_size == self.buffer.shape[0]:
                self._flush_cherenkov_bunch_buffer()

    def _flush_cherenkov_bunch_buffer(self):
        self.tarw(
            filename=CHERENKOV_BLOCK_FILENAME.format(
                run_number=self.run_number,
                event_number=self.event_number,
                cherenkov_block_number=self.cherenkov_block_number
            ),
            filebytes=self.buffer[0:self.buffer_size].tobytes()
        )
        self.cherenkov_block_number += 1
        self.buffer_size = 0

    def tarw(self, filename, filebytes):
        with io.BytesIO() as buff:
            info = tarfile.TarInfo(filename)
            info.size = buff.write(filebytes)
            buff.seek(0)
            self.tar.addfile(info, buff)

    def __exit__(self):
        self.tar.close()

    def __repr__(self):
        out = "{:s}(path='{:s}')".format(self.__class__.__name__, self.path)
        return out


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
        self.run_number = int(self.runh[I.RUNH.RUN_NUMBER])

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
            bunch_tape = BunchTapeReader(run=self)
            for cherenkov_block in bunch_tape:
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


RUNH_FILENAME = "{run_number:09d}/RUNH.float32"
EVTH_FILENAME = "{run_number:09d}/{event_number:09d}/EVTH.float32"
CHERENKOV_BLOCK_FILENAME = "{run_number:09d}/{event_number:09d}/{cherenkov_block_number:09d}.cer.x8.float32"


def is_cherenkov_block_path(path):
    return is_match(CHERENKOV_BLOCK_FILENAME, path)


def is_evth_path(path):
    return is_match(EVTH_FILENAME, path)


def is_runh_path(path):
    return is_match(RUNH_FILENAME, path)


def parse_run_number(path):
    return int(path[0 : 0 + 9])


def parse_event_number(path):
    return int(path[10 : 10 + 9])


def parse_cherenkov_block_number(path):
    return int(path[20 : 20 + 9])


def read_runh(tar, tarinfo):
    assert is_runh_path(tarinfo.name)
    runh_bin = tar.extractfile(tarinfo).read()
    runh = np.frombuffer(runh_bin, dtype=np.float32)
    assert runh.shape[0] == 273
    assert runh[I.RUNH.MARKER] == I.RUNH.MARKER_FLOAT32
    assert runh[I.RUNH.RUN_NUMBER] == parse_run_number(tarinfo.name)
    return runh


def write_runh(tar, runh, run_number):
    assert runh.dtype == np.float32
    assert runh.shape[0] == 273
    assert runh[I.RUNH.MARKER] == I.RUNH.MARKER_FLOAT32
    runh_run_number = int(runh[I.RUNH.RUN_NUMBER])
    assert runh_run_number == run_number
    tar_write(
        tar=tar,
        filename=RUNH_FILENAME.format(run_number=run_number),
        filebytes=runh.tobytes()
    )


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


def write_evth(tar, evth, run_number, event_number):
    assert evth.dtype == np.float32
    assert evth.shape[0] == 273
    assert evth[I.EVTH.MARKER] == I.EVTH.MARKER_FLOAT32
    assert evth[I.EVTH.RUN_NUMBER] == run_number
    assert evth[I.EVTH.EVENT_NUMBER] == event_number
    tar_write(
        tar=tar,
        filename=EVTH_FILENAME.format(
            run_number=run_number, event_number=event_number,
        ),
        filebytes=evth.tobytes()
    )


def read_cherenkov_bunch_block(tar, tarinfo):
    assert is_cherenkov_block_path(tarinfo.name)
    bunches_bin = tar.extractfile(tarinfo).read()
    bunches = np.frombuffer(bunches_bin, dtype=np.float32)
    num_bunches = bunches.shape[0] // (8)
    return np.reshape(bunches, newshape=(num_bunches, 8))


def tar_write(tar, filename, filebytes):
    with io.BytesIO() as buff:
        info = tarfile.TarInfo(filename)
        info.size = buff.write(filebytes)
        buff.seek(0)
        tar.addfile(info, buff)
