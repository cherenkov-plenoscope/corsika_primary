import numpy as np
import subprocess
import os
import glob
from . import I

def bunches_SI_units(bunches):
    b = np.zeros(shape=bunches.shape, dtype=np.float32)
    b[:, I.BUNCH.X] = bunches[:, I.BUNCH.X] * 1e-2  # cm -> m
    b[:, I.BUNCH.Y] = bunches[:, I.BUNCH.Y] * 1e-2  # cm -> m
    b[:, I.BUNCH.CX] = bunches[:, I.BUNCH.CX]
    b[:, I.BUNCH.CY] = bunches[:, I.BUNCH.CY]
    b[:, I.BUNCH.TIME] = bunches[:, I.BUNCH.TIME] * 1e-9  # ns -> s
    b[:, I.BUNCH.ZEM] = bunches[:, I.BUNCH.ZEM] * 1e-2  # cm -> m
    b[:, I.BUNCH.BSIZE] = bunches[:, I.BUNCH.BSIZE]
    b[:, I.BUNCH.WVL] = np.abs(bunches[:, I.BUNCH.WVL]) * 1e-9  # nm -> m
    return b


def eventio_to_simpleio(
    merlict_eventio_converter,
    eventio_path,
    simpleio_path
):
    rc = subprocess.call(
        [
            merlict_eventio_converter,
            "-i",
            ori_run_eventio_path,
            "-o",
            ori_run_path,
        ]
    )
    assert rc == 0


class SimpleIoRun():
    def __init__(self, path):
        """
        Parameters
        ----------
        path        The path to the directory representing the run.
        """
        self.path = os.path.abspath(path)
        if not os.path.isdir(self.path):
            raise NotADirectoryError(self.path)

        with open(os.path.join(path, 'corsika_run_header.bin'), "rb") as f:
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

        evth_path = os.path.join(event_path, 'corsika_event_header.bin')
        with open(evth_path, "rb") as f:
            evth = np.frombuffer(f.read(), dtype=np.float32)

        bunches_path = os.path.join(event_path, 'air_shower_photon_bunches.bin')
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
        out = self.__class__.__name__ + '(path={:s})'.format(self.path)
        return out
