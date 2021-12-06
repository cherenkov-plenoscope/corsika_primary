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
