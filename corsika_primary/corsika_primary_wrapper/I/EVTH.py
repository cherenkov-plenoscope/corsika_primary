import struct

MARKER_FLOAT32 = struct.unpack("f", "EVTH".encode())[0]

MARKER = 1 - 1
EVENT_NUMBER = 2 - 1
PARTICLE_ID = 3 - 1
TOTAL_ENERGY_GEV = 4 - 1
STARTING_DEPTH_G_PER_CM2 = 5 - 1
NUMBER_OF_FIRST_TARGET_IF_FIXED = 6 - 1
Z_FIRST_INTERACTION_CM = 7 - 1
PX_MOMENTUM_GEV_PER_C = 8 - 1
PY_MOMENTUM_GEV_PER_C = 9 - 1
PZ_MOMENTUM_GEV_PER_C = 10 - 1
ZENITH_RAD = 11 - 1
AZIMUTH_RAD = 12 - 1

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


EARTH_MAGNETIC_FIELD_X_UT = 71 - 1
EARTH_MAGNETIC_FIELD_X_UT = 72 - 1
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
