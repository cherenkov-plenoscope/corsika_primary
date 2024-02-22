import spherical_coordinates
import numpy as np
from .I import BUNCH


def impact(x, y):
    """
    parameters
    ----------
    x : float
        Impact position on observation level in x, this is I.BUNCH.X_CM.
    y : float
        Impact position on observation level in y, this is I.BUNCH.Y_CM.

    returns
    -------
    impact : np.array, shape = (3, )
        Impact vector of photon on observation level.
    """
    return np.array([x, y, 0])


def momentum(ux, vy):
    """
    parameters
    ----------
    ux : float
        direction cosine of photon. Corresponds to I.BUNCH.UX_1
    vy : float
        direction cosine of photon. Corresponds to I.BUNCH.VY_1

    returns
    -------
    momentum : np.array, shape = (3, )
        Momentmum vector of photon. This is the photon's direction of motion.

    KIT-CORSIKA coordinate-system
    -----------------------------

    *                   /| z-axis                                              *
    *                   |                                                      *
    *                   || p                                                   *
    *                   | | a                                                  *
    *                   |  | r                                                 *
    *                   |   | t                                                *
    *                   |    | i                                               *
    *                   |     | c                                              *
    *                   |      | l                                             *
    *                   |       | e                                            *
    *                   |        |                                             *
    *                   |  theta  | m                                          *
    *                   |       ___| o                                         *
    *                   |___----    | m      ___                               *
    *                   |            | e       /| y-axis (west)                *
    *                   |             | n    /                                 *
    *                   |              | t /                                   *
    *                   |               |/u                                    *
    *                   |              / | m                                   *
    *                   |            /    |                                    *
    *                   |          /       |                                   *
    *                   |        /__________|                                  *
    *                   |      /      ___---/                                  *
    *                   |    /   __---    /                                    *
    *                   |  /__--- phi | /                                      *
    *   ________________|/--__________/______| x-axis (north)                  *
    *                  /|                    /                                 *
    *                /  |                                                      *
    *              /    |                                                      *
    *            /                                                             *
    *                                                                          *
    *                                                                          *
        Extensive Air Shower Simulation with CORSIKA, Figure 1, page 114
        (Version 7.6400 from December 27, 2017)

        Direction-cosines:

        u = sin(theta) * cos(phi)
        v = sin(theta) * sin(phi)

        The zenith-angle theta opens relative to the negative z-axis.

        It is the momentum of the Cherenkov-photon, which is pointing
        down towards the observation-plane.

    """
    z = spherical_coordinates.restore_cz(cx=ux, cy=vy)
    TOWARDS_XY_PLANE = -1.0
    return np.array([ux, vy, TOWARDS_XY_PLANE * z])
