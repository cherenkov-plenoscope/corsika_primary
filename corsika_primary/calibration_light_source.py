import numpy as np
from . import random
from . import I


def draw_parallel_and_isochor_bunches(
    cx,
    cy,
    aperture_radius,
    wavelength,
    size,
    prng,
    speed_of_light=299792458,
):
    assert aperture_radius >= 0
    assert wavelength >= 0
    assert size >= 0

    bun = np.zeros(shape=(size, I.BUNCH.NUM_FLOAT32), dtype=np.float32)

    for i in range(size):
        (
            bun[i, I.BUNCH.X],
            bun[i, I.BUNCH.Y]
        ) = random.distributions.draw_x_y_in_disc(
            prng=prng,
            radius=aperture_radius
        )

    bun[:, I.BUNCH.CX] = cx
    bun[:, I.BUNCH.CY] = cy

    delta_path_lengths = (
        bun[:, I.BUNCH.CX] * bun[:, I.BUNCH.X]
        + bun[:, I.BUNCH.CY] * bun[:, I.BUNCH.Y]
    )
    bun[:, I.BUNCH.TIME] = delta_path_lengths / speed_of_light

    bun[:, I.BUNCH.WVL] = wavelength
    bun[:, I.BUNCH.BSIZE] = 1.0
    bun[:, I.BUNCH.ZEM] = 1.0

    # to cgs units
    # ------------
    bun[:, I.BUNCH.X] *= 1e2  # m -> cm
    bun[:, I.BUNCH.Y] *= 1e2  # m -> cm

    bun[:, I.BUNCH.TIME] *= 1e9  # s -> ns
    bun[:, I.BUNCH.ZEM] *= 1e2  # m -> cm

    bun[:, I.BUNCH.WVL] *= 1e9 # m -> nm
    return bun
