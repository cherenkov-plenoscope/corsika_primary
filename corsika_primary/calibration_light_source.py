import numpy as np
from . import random
from . import I


def draw_parallel_and_isochor_bunches(
    cx, cy, aperture_radius, wavelength, size, prng, speed_of_light=299792458,
):
    """
    Returns photon-bunches emitted by a star-like source of light.
    The photons are meant to arrive in the same pixel in the same moment.
    This means, they travel in a plane perpendicular to their direction
    of motion.

    Parameters
    ----------
    cx : float
        Angle of incident w.r.t. x-axis in rad.
    cy : float
        Angle of incident w.r.t. y-axis in rad.
    aperture_radius : float >= 0
        Radius of the disc illuminated by the photons on the aperture's
        principal plane a.k.a. observation-level.
    wavelength : float >= 0
        The wavelength of the photon-bunches.
    size : int >= 0
        The number of photon-bunches.
    prng : numpy.random.Generator

    speed_of_light : float
        The photon's speed right above the aperture / obersavtion-level.
    """
    assert aperture_radius >= 0
    assert wavelength >= 0
    assert size >= 0

    bun = np.zeros(shape=(size, I.BUNCH.NUM_FLOAT32), dtype=np.float32)

    for i in range(size):
        (
            bun[i, I.BUNCH.X],
            bun[i, I.BUNCH.Y],
        ) = random.distributions.draw_x_y_in_disc(
            prng=prng, radius=aperture_radius
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

    bun[:, I.BUNCH.WVL] *= 1e9  # m -> nm
    return bun
