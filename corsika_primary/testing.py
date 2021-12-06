import numpy as np
import subprocess
import os
import glob
from . import I


class TmpDebugDir:
    def __init__(self, debug_dir, suffix=None, prefix="corsika_primary"):
        if debug_dir:
            self.debug = True
            self.handle = None
            self.name = os.path.join(debug_dir, suffix)
            os.makedirs(self.name, exist_ok=True)
        else:
            self.debug = False
            self.tmp_dir_handle = tempfile.TemporaryDirectory(
                prefix=prefix, suffix=suffix
            )
            self.name = self.tmp_dir_handle.name

    def cleanup_when_no_debug(self):
        if not self.debug:
            self.tmp_dir_handle.cleanup()


def eventio_to_simpleio(
    merlict_eventio_converter, eventio_path, simpleio_path
):
    rc = subprocess.call(
        [merlict_eventio_converter, "-i", eventio_path, "-o", simpleio_path,]
    )
    assert rc == 0


class SimpleIoRun:
    def __init__(self, path):
        """
        Parameters
        ----------
        path        The path to the directory representing the run.
        """
        self.path = os.path.abspath(path)
        if not os.path.isdir(self.path):
            raise NotADirectoryError(self.path)

        with open(os.path.join(path, "corsika_run_header.bin"), "rb") as f:
            self.runh = np.frombuffer(f.read(), dtype=np.float32)

        self.event_ids = []
        for p in glob.glob(os.path.join(path, "*")):
            if os.path.isdir(p) and os.path.basename(p).isdigit():
                self.event_ids.append(int(os.path.basename(p)))
        self.event_ids = np.array(self.event_ids)
        self.event_ids.sort()
        self.next_event_id = self.event_ids[0]

    def __next__(self):
        event_path = os.path.join(self.path, str(self.next_event_id))
        if not os.path.isdir(event_path):
            raise StopIteration

        evth_path = os.path.join(event_path, "corsika_event_header.bin")
        with open(evth_path, "rb") as f:
            evth = np.frombuffer(f.read(), dtype=np.float32)

        bunches_path = os.path.join(
            event_path, "air_shower_photon_bunches.bin"
        )
        with open(bunches_path, "rb") as f:
            bunches = np.frombuffer(f.read(), dtype=np.float32)

        assert bunches.shape[0] % 8 == 0
        num_bunches = bunches.shape[0] // 8
        bunches = bunches.reshape((num_bunches, 8))

        self.next_event_id += 1
        return (evth, bunches)

    def __iter__(self):
        return self

    def __exit__(self):
        pass

    def __repr__(self):
        out = self.__class__.__name__ + "(path={:s})".format(self.path)
        return out


def parse_random_seeds_from_corsika_stdout(stdout):
    """
    Returns a list of random-number-generator states at the begin of each
    event.
    Does not contain all events. CORSIKA does not print this for all events.
    Only use this when CORSIKA's Cherenkov-output is broken.

    parameters
    ----------
    stdout : str
        CORSIKA's stdout.
    """
    events = []
    MARKER = " AND RANDOM NUMBER GENERATOR AT BEGIN OF EVENT :"
    lines = stdout.split("\n")
    idx = 0
    while idx < len(lines):
        if MARKER in lines[idx]:
            _seeds = [None] * NUM_RANDOM_SEQUENCES
            _calls = [None] * NUM_RANDOM_SEQUENCES
            _billions = [None] * NUM_RANDOM_SEQUENCES
            event_number = int(lines[idx][49:57])
            assert len(events) + 1 == event_number

            for seq in np.arange(0, NUM_RANDOM_SEQUENCES):
                is_sequence = False
                while idx < len(lines) and not is_sequence:
                    idx += 1
                    match = " SEQUENCE =  {:d}  SEED =".format(seq + 1)
                    is_sequence = str.find(lines[idx], match) == 0
                _seeds[seq] = int(lines[idx][22:33])
                _calls[seq] = int(lines[idx][41:52])
                _billions[seq] = int(lines[idx][63:73])

            state = []
            for seq in np.arange(0, NUM_RANDOM_SEQUENCES):
                state.append(
                    {
                        "SEED": np.int32(_seeds[seq]),
                        "CALLS": np.int32(_calls[seq]),
                        "BILLIONS": np.int32(_billions[seq]),
                    }
                )
            events.append(state)
        idx += 1
    return events


def parse_num_bunches_from_corsika_stdout(stdout):
    """
    Returns the number of bunches, not photons of each event.
    Does not contain all events. CORSIKA does not print this for all events.
    Only use this when CORSIKA's Cherenkov-output is broken.

    parameters
    ----------
    stdout : str
        CORSIKA's stdout.
    """
    marker = " Total number of photons in shower:"
    nums = []
    lines = stdout.split("\n")
    for ll in range(len(lines)):
        pos = lines[ll].find(marker)
        if pos == 0:
            work_line = lines[ll][len(marker) : -1]
            pos_2nd_in = work_line.find("in")
            work_line = work_line[pos_2nd_in + 2 : -len("bunch") - 1]
            nums.append(int(float(work_line)))
    return nums