import struct
import numpy as np
import spherical_coordinates


MARKER_FLOAT32 = struct.unpack("f", "EVTH".encode())[0]

# See Table 9 on pages 118, 119 in the CORSIKA 7.56 manual

MARKER = 1 - 1
EVENT_NUMBER = 2 - 1
PARTICLE_ID = 3 - 1
TOTAL_ENERGY_GEV = 4 - 1
STARTING_DEPTH_G_PER_CM2 = 5 - 1
NUMBER_OF_FIRST_TARGET_IF_FIXED = 6 - 1
Z_FIRST_INTERACTION_CM = 7 - 1
PX_MOMENTUM_GEV_PER_C = 8 - 1
PY_MOMENTUM_GEV_PER_C = 9 - 1
PZ_MOMENTUM_IN_NEGATIVE_Z_DIRECTION_GEV_PER_C = 10 - 1
THETA_RAD = 11 - 1
PHI_RAD = 12 - 1
# The manual says theta is the zenith and phi is the azimuth.
# However, it is more say to say that theta is relatesd to the zenith so
# one does not confuse it with common definition of 'zenith distance'.
# Zenith distance opens from the positive z-axis.
# But CORSIKA's theta/zenith angle opens from the negative z-axis.

NUM_DIFFERENT_RANDOM_SEQUENCES = 13 - 1


def RANDOM_SEED(sequence):
    assert sequence >= 1
    assert sequence <= 10
    return (11 + 3 * sequence) - 1


def RANDOM_SEED_CALLS(sequence):
    assert sequence >= 1
    assert sequence <= 10
    return (12 + 3 * sequence) - 1


def RANDOM_SEED_MILLIONS(sequence):
    """
    This is actually 10**6, but the input to corsika is billions 10**9
    """
    assert sequence >= 1
    assert sequence <= 10
    return (13 + 3 * sequence) - 1


RUN_NUMBER = 44 - 1
DATE_OF_BEGIN_RUN = 45 - 1
VERSION_OF_PROGRAM = 46 - 1

NUM_OBSERVATION_LEVELS = 47 - 1


def HEIGHT_OBSERVATION_LEVEL(level):
    assert level >= 1
    assert level <= 10
    return (47 + level) - 1


ENERGY_LOWER_LIMIT = 59 - 1
ENERGY_UPPER_LIMIT = 60 - 1

EARTH_MAGNETIC_FIELD_X_UT = 71 - 1
EARTH_MAGNETIC_FIELD_X_UT = 72 - 1

CHERENKOV_FLAG = 77 - 1

ANGLE_X_MAGNETIG_NORTH_RAD = 93 - 1
NUM_REUSES_OF_CHERENKOV_EVENT = 98 - 1


def X_CORE_CM(reuse):
    assert reuse >= 1
    assert reuse <= 20
    return (98 + reuse) - 1


def Y_CORE_CM(reuse):
    assert reuse >= 1
    assert reuse <= 20
    return (118 + reuse) - 1


STARTING_HEIGHT_CM = 158 - 1


def get_momentum_vector_GeV_per_c(evth):
    momentum = np.zeros(3, dtype=np.float64)
    momentum[0] = evth[PX_MOMENTUM_GEV_PER_C]
    momentum[1] = evth[PY_MOMENTUM_GEV_PER_C]
    _mom_in_negative_z = evth[PZ_MOMENTUM_IN_NEGATIVE_Z_DIRECTION_GEV_PER_C]
    momentum[2] = (-1) * _mom_in_negative_z
    return momentum


def get_direction_uxvywz(evth):
    mom = get_momentum_vector_GeV_per_c(evth=evth)
    return mom / np.linalg.norm(mom)


def get_direction_phi_theta(evth):
    return evth[PHI_RAD], evth[THETA_RAD]


def get_pointing_cxcycz(evth):
    ux, vy, wz = get_direction_uxvywz(evth=evth)
    cx = spherical_coordinates.corsika.ux_to_cx(ux=ux)
    cy = spherical_coordinates.corsika.vy_to_cy(vy=vy)
    cz = spherical_coordinates.corsika.wz_to_cz(wz=wz)
    return np.array([cx, cy, cz])


def get_pointing_az_zd(evth):
    return spherical_coordinates.corsika.phi_theta_to_az_zd(
        phi_rad=evth[PHI_RAD],
        theta_rad=evth[THETA_RAD],
    )
