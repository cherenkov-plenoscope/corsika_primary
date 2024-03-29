import numpy as np
import spherical_coordinates


def draw_power_law(prng, lower_limit, upper_limit, power_slope, num_samples):
    """
    Parameters
    ----------
    prng : numpy.random.Generator
        Pseudo random number generator
    lower_limit : float
        Lower limit of the distribution to draw from.
    upper_limit : float
        Upper limit of the distribution to draw from.
    power_slope : float
        Slope of the power law to draw from.
    num_samples : int
        The number of samples to be drawn.

    Returns
    -------
    x : numpy.array, floats
        Values between 'lower_limit' and 'upper_limit' occuring a ccording to
        a power law with slope 'power_slope'.
    """
    # Adopted from CORSIKA
    rd = prng.uniform(size=num_samples)
    if power_slope != -1.0:
        ll = lower_limit ** (power_slope + 1.0)
        ul = upper_limit ** (power_slope + 1.0)
        slex = 1.0 / (power_slope + 1.0)
        return (rd * ul + (1.0 - rd) * ll) ** slex
    else:
        ll = upper_limit / lower_limit
        return lower_limit * ll**rd


def draw_zenith_distance(
    prng, min_zenith_distance, max_zenith_distance, num_samples=1
):
    v_min = (np.cos(min_zenith_distance) + 1) / 2
    v_max = (np.cos(max_zenith_distance) + 1) / 2
    v = prng.uniform(low=v_min, high=v_max, size=num_samples)
    return np.arccos(2 * v - 1)


def draw_azimuth_zenith_in_viewcone(
    prng,
    azimuth_rad,
    zenith_rad,
    min_scatter_opening_angle_rad,
    max_scatter_opening_angle_rad,
    max_zenith_rad=np.deg2rad(70),
    max_iterations=1000 * 1000,
):
    """
    Draw a random pointing (azimuth, zenith distance) from within a viewcone.

    Parameters
    ----------
    prng : numpy.random.Generator
        Pseudo random number generator
    azimuth_rad : float
        Azimuth pointing of viewcone.
    zenith_rad : float
        Zenith distance pointing of viewcone.
    min_scatter_opening_angle_rad : float
        Minimum half angle of viewcone to draw from.
    max_scatter_opening_angle_rad : float
        Maximum half angle of viewcone to draw from.
    max_zenith_rad : float
        The max. zenith distance a drawn pointing must have.
    max_iterations : int
        Limiting the max zenith distance is done with rejection sampling.
        This max_iterations limit the max. number of rejections.

    Returns
    -------
    (azimuth, zenith distance) : (float, float)
        In rad.
    """
    assert min_scatter_opening_angle_rad >= 0.0
    assert max_scatter_opening_angle_rad >= min_scatter_opening_angle_rad
    assert max_zenith_rad >= 0.0

    zenith_too_large = True
    iteration = 0
    while zenith_too_large:
        az, zd = spherical_coordinates.random.uniform_az_zd_in_cone(
            prng=prng,
            azimuth_rad=azimuth_rad,
            zenith_rad=zenith_rad,
            min_half_angle_rad=min_scatter_opening_angle_rad,
            max_half_angle_rad=max_scatter_opening_angle_rad,
        )
        if zd <= max_zenith_rad:
            zenith_too_large = False
        iteration += 1
        if iteration > max_iterations:
            raise RuntimeError("Rejection-sampling failed.")
    return az, zd


def draw_x_y_in_disc(prng, radius):
    """
    Draw a random position within a disc.

    Parameters
    ----------
    prng : numpy.random.Generator
        Pseudo random number generator
    radius : float
        Radius of the disc.

    Returns
    -------
    (x, y) : (float, float)
        A random position on the xy plane within a radius 'radius' from the
        origin.
    """
    rho = np.sqrt(prng.uniform(low=0.0, high=1.0)) * radius
    phi = prng.uniform(low=0.0, high=2.0 * np.pi)
    x = rho * np.cos(phi)
    y = rho * np.sin(phi)
    return x, y
