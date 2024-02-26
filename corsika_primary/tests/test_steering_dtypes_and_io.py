import pytest
import corsika_primary as cpw
import inspect
import numpy as np
import tempfile
import os

i4 = np.int32
i8 = np.int64
f8 = np.float64


@pytest.fixture()
def debug_dir(pytestconfig):
    return pytestconfig.getoption("debug_dir")


def uniform(prng, low, high):
    return prng.uniform(low=low, high=high, size=1)[0]


def make_dummy_run_steering(run_id, prng):
    run = {
        "run_id": i8(run_id),
        "event_id_of_first_event": i8(uniform(prng=prng, low=0, high=100)),
        "observation_level_asl_m": f8(uniform(prng=prng, low=0, high=5000)),
        "earth_magnetic_field_x_muT": f8(uniform(prng=prng, low=0, high=25)),
        "earth_magnetic_field_z_muT": f8(uniform(prng=prng, low=0, high=25)),
        "atmosphere_id": i8(uniform(prng=prng, low=0, high=10)),
        "energy_range": {
            "start_GeV": f8(uniform(prng=prng, low=1, high=2)),
            "stop_GeV": f8(uniform(prng=prng, low=10, high=20)),
        },
    }
    run["random_seed"] = []
    for j in range(cpw.random.seed.NUM_RANDOM_SEQUENCES):
        state = {
            "SEED": i4(uniform(prng=prng, low=0, high=100)),
            "CALLS": i4(uniform(prng=prng, low=0, high=100)),
            "BILLIONS": i4(uniform(prng=prng, low=0, high=100)),
        }
        run["random_seed"].append(state)
    return run


def make_dummy_primaries(num, prng):
    primaries = []
    for i in range(num):
        prm = {}
        prm["particle_id"] = f8(uniform(prng=prng, low=0, high=100))
        prm["energy_GeV"] = f8(1 + uniform(prng=prng, low=0, high=5))
        prm["theta_rad"] = f8(uniform(prng=prng, low=0, high=1))
        prm["phi_rad"] = f8(uniform(prng=prng, low=0, high=2) - 1)
        prm["depth_g_per_cm2"] = f8(0.0)
        cpw.steering.assert_dtypes_primary_dict(prm)
        primaries.append(prm)
    return primaries


def make_dummy_event_seeds(num, prng):
    event_seeds = {}
    for event_id in np.arange(1, num + 1):
        event_seeds[event_id] = []
        for seq in range(cpw.random.seed.NUM_RANDOM_SEQUENCES):
            state = {
                "SEED": i4(uniform(prng=prng, low=0, high=1e6)),
                "CALLS": i4(uniform(prng=prng, low=0, high=1e6)),
                "BILLIONS": i4(uniform(prng=prng, low=0, high=1e6)),
            }
            event_seeds[event_id].append(state)
    return event_seeds


def primary_is_equal(a, b):
    cpw.steering.assert_dtypes_primary_dict(a)
    cpw.steering.assert_dtypes_primary_dict(b)
    if a["particle_id"] != b["particle_id"]:
        return False
    if a["energy_GeV"] != b["energy_GeV"]:
        return False
    if a["theta_rad"] != b["theta_rad"]:
        return False
    if a["phi_rad"] != b["phi_rad"]:
        return False
    if a["depth_g_per_cm2"] != b["depth_g_per_cm2"]:
        return False
    return True


def test_primaries_dict_to_bytes_to_dict():
    prng = np.random.Generator(np.random.PCG64(42))
    NUM = 1337
    primaries_orig = make_dummy_primaries(num=NUM, prng=prng)
    primary_bytes = cpw.steering.primary_dicts_to_bytes(
        primary_dicts=primaries_orig
    )
    primaries_back = cpw.steering.primary_bytes_to_dicts(
        primary_bytes=primary_bytes
    )
    for i in range(NUM):
        orig = primaries_orig[i]
        back = primaries_back[i]
        assert primary_is_equal(orig, back)


def test_primary_bytes_extract_slice():
    prng = np.random.Generator(np.random.PCG64(402))
    NUM = 1337
    primaries_orig = make_dummy_primaries(num=NUM, prng=prng)
    primary_bytes = cpw.steering.primary_dicts_to_bytes(
        primary_dicts=primaries_orig
    )
    for i in range(NUM):
        prm_pytes = cpw.steering.primary_bytes_by_idx(
            primary_bytes=primary_bytes, idx=i
        )
        prm_back = cpw.steering.primary_bytes_to_dicts(primary_bytes=prm_pytes)
        orig = primaries_orig[i]
        back = prm_back[0]
        assert primary_is_equal(orig, back)


def test_steering_dict_io(debug_dir):
    tmp = cpw.testing.TmpDebugDir(
        debug_dir=debug_dir,
        suffix=inspect.getframeinfo(inspect.currentframe()).function,
    )

    NUM_RUNS = 42
    NUM_EVENTS = 137
    prng = np.random.Generator(np.random.PCG64(42))

    orig = {}
    for rr in range(NUM_RUNS):
        run_id = rr + 1
        orig[run_id] = {
            "run": make_dummy_run_steering(run_id=run_id, prng=prng),
            "primaries": make_dummy_primaries(num=NUM_EVENTS, prng=prng),
        }

    path = os.path.join(tmp.name, "steering.tar")
    cpw.steering.write_steerings(path=path, runs=orig)
    back = cpw.steering.read_steerings(path=path)

    for run_id in orig:
        assert orig[run_id]["run"] == back[run_id]["run"]
        assert orig[run_id]["primaries"] == back[run_id]["primaries"]

    tmp.cleanup_when_no_debug()
