import numpy as np


def simpleio_bunches_to_array(bunches):
    num_bunches = bunches.x.shape[0]
    b = np.zeros(shape=(num_bunches, 8), dtype=np.float32)
    b[:, cpw.IX] = bunches.x
    b[:, cpw.IY] = bunches.y
    b[:, cpw.ICX] = bunches.cx
    b[:, cpw.ICY] = bunches.cy
    b[:, cpw.ITIME] = bunches.arrival_time_since_first_interaction
    b[:, cpw.IZEM] = bunches.emission_height
    b[:, cpw.IBSIZE] = bunches.probability_to_reach_observation_level
    b[:, cpw.IWVL] = np.abs(bunches.wavelength)
    return b


def tario_bunches_to_array(bunches):
    b = np.zeros(shape=bunches.shape, dtype=np.float32)
    b[:, cpw.IX] = bunches[:, cpw.IX] * 1e-2  # cm -> m
    b[:, cpw.IY] = bunches[:, cpw.IY] * 1e-2  # cm -> m
    b[:, cpw.ICX] = bunches[:, cpw.ICX]
    b[:, cpw.ICY] = bunches[:, cpw.ICY]
    b[:, cpw.ITIME] = bunches[:, cpw.ITIME] * 1e-9  # ns -> s
    b[:, cpw.IZEM] = bunches[:, cpw.IZEM] * 1e-2  # cm -> m
    b[:, cpw.IBSIZE] = bunches[:, cpw.IBSIZE]
    b[:, cpw.IWVL] = np.abs(bunches[:, cpw.IWVL]) * 1e-9  # nm -> m
    return b
