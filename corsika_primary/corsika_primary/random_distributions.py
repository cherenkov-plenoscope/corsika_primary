import numpy as np


def draw_power_law(prng, lower_limit, upper_limit, power_slope, num_samples):
    # Adopted from CORSIKA
    rd = prng.uniform(size=num_samples)
    if power_slope != -1.0:
        ll = lower_limit ** (power_slope + 1.0)
        ul = upper_limit ** (power_slope + 1.0)
        slex = 1.0 / (power_slope + 1.0)
        return (rd * ul + (1.0 - rd) * ll) ** slex
    else:
        ll = upper_limit / lower_limit
        return lower_limit * ll ** rd


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
    assert min_scatter_opening_angle_rad >= 0.0
    assert max_scatter_opening_angle_rad >= min_scatter_opening_angle_rad
    assert max_zenith_rad >= 0.0
    # Adopted from CORSIKA
    zenith_too_large = True
    iteration = 0
    while zenith_too_large:
        rd1, rd2 = prng.uniform(size=2)
        ct1 = np.cos(min_scatter_opening_angle_rad)
        ct2 = np.cos(max_scatter_opening_angle_rad)
        ctt = rd2 * (ct2 - ct1) + ct1
        theta = np.arccos(ctt)
        phi = rd1 * np.pi * 2.0
        # TEMPORARY CARTESIAN COORDINATES
        xvc1 = np.cos(phi) * np.sin(theta)
        yvc1 = np.sin(phi) * np.sin(theta)
        zvc1 = np.cos(theta)
        # ROTATE AROUND Y AXIS
        xvc2 = xvc1 * np.cos(zenith_rad) + zvc1 * np.sin(zenith_rad)
        yvc2 = yvc1
        zvc2 = zvc1 * np.cos(zenith_rad) - xvc1 * np.sin(zenith_rad)
        zd = np.arccos(zvc2)
        if zd <= max_zenith_rad:
            zenith_too_large = False
        iteration += 1
        if iteration > max_iterations:
            raise RuntimeError("Rejection-sampling failed.")
    if xvc2 != 0.0 or yvc2 != 0.0:
        az = np.arctan2(yvc2, xvc2) + azimuth_rad
    else:
        az = azimuth_rad
    if az >= np.pi * 2.0:
        az -= np.pi * 2.0
    if az < 0.0:
        az += np.pi * 2.0
    return az, zd


def draw_x_y_in_disc(prng, radius):
    rho = np.sqrt(prng.uniform(low=0.0, high=1.0)) * radius
    phi = prng.uniform(low=0.0, high=2.0 * np.pi)
    x = rho * np.cos(phi)
    y = rho * np.sin(phi)
    return x, y
