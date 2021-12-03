import numpy as np
import simpleio
from . import I


def simpleio_bunches_to_array(bunches):
    num_bunches = bunches.x.shape[0]
    b = np.zeros(shape=(num_bunches, 8), dtype=np.float32)
    b[:, I.BUNCH.X] = bunches.x
    b[:, I.BUNCH.Y] = bunches.y
    b[:, I.BUNCH.CX] = bunches.cx
    b[:, I.BUNCH.CY] = bunches.cy
    b[:, I.BUNCH.TIME] = bunches.arrival_time_since_first_interaction
    b[:, I.BUNCH.ZEM] = bunches.emission_height
    b[:, I.BUNCH.BSIZE] = bunches.probability_to_reach_observation_level
    b[:, I.BUNCH.WVL] = np.abs(bunches.wavelength)
    return b


def tario_bunches_to_array(bunches):
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


def ttt(simpleio_path):
    event_seeds = {}
    pool_hashes = {}
    run = simpleio.SimpleIoRun(simpleio_path)
    for event_idx in range(len(run)):
        event = run[event_idx]
        evth = event.header.raw
        bunches = simpleio_bunches_to_array(event.cherenkov_photon_bunches)
