import corsika_primary_wrapper as cpw
import numpy as np
import tempfile
import os

i4 = np.int32
i8 = np.int64
f8 = np.float64


def make_dummy_run_steering(run_id, prng):
    run = {
        "run_id": i8(run_id),
        "event_id_of_first_event": i8(prng.uniform(100)),
        "observation_level_asl_m": f8(prng.uniform(5000)),
        "earth_magnetic_field_x_muT": f8(prng.uniform(25)),
        "earth_magnetic_field_z_muT": f8(prng.uniform(25)),
        "atmosphere_id": i8(prng.uniform(10)),
        "energy_range": {
            "start_GeV": f8(prng.uniform(low=1, high=2)),
            "stop_GeV": f8(prng.uniform(low=10, high=20))
        },
    }
    return run


def make_dummy_primaries(num, prng):
    primaries = []
    for i in range(num):
        prm = {}
        prm["particle_id"] = f8(prng.uniform(100))
        prm["energy_GeV"] = f8(1 + prng.uniform(5))
        prm["zenith_rad"] = f8(prng.uniform(1))
        prm["azimuth_rad"] = f8(prng.uniform(2) - 1)
        prm["depth_g_per_cm2"] = f8(0.0)
        prm["random_seed"] = []
        for j in range(4):
            seeds = {
                "SEED": i4(prng.uniform(100)),
                "CALLS": i4(prng.uniform(100)),
                "BILLIONS": i4(prng.uniform(100)),
            }
            prm["random_seed"].append(seeds)
        cpw.steering.assert_dtypes_primary_dict(prm)
        primaries.append(prm)
    return primaries


def primary_is_equal(a, b):
    cpw.steering.assert_dtypes_primary_dict(a)
    cpw.steering.assert_dtypes_primary_dict(b)
    if a["particle_id"] != b["particle_id"]:
        return False
    if a["energy_GeV"] != b["energy_GeV"]:
        return False
    if a["zenith_rad"] != b["zenith_rad"]:
        return False
    if a["azimuth_rad"] != b["azimuth_rad"]:
        return False
    if a["depth_g_per_cm2"] != b["depth_g_per_cm2"]:
        return False
    for j in range(4):
        for key in ["SEED", "CALLS", "BILLIONS"]:
            if a["random_seed"][j][key] != b["random_seed"][j][key]:
                return False
    return True


def test_primaries_dict_to_bytes_to_dict():
    prng = np.random.Generator(np.random.PCG64(42))
    NUM = 1337
    primaries_orig = make_dummy_primaries(num=NUM, prng=prng)
    primary_bytes = cpw.steering.primary_dicts_to_bytes(primary_dicts=primaries_orig)
    primaries_back = cpw.steering.primary_bytes_to_dicts(primary_bytes=primary_bytes)
    for i in range(NUM):
        orig = primaries_orig[i]
        back = primaries_back[i]
        assert primary_is_equal(orig, back)


def test_primary_bytes_extract_slice():
    prng = np.random.Generator(np.random.PCG64(402))
    NUM = 1337
    primaries_orig = make_dummy_primaries(num=NUM, prng=prng)
    primary_bytes = cpw.steering.primary_dicts_to_bytes(primary_dicts=primaries_orig)
    for i in range(NUM):
        prm_pytes = cpw.steering.primary_bytes_by_idx(primary_bytes=primary_bytes, idx=i)
        prm_back = cpw.steering.primary_bytes_to_dicts(primary_bytes=prm_pytes)
        orig = primaries_orig[i]
        back = prm_back[0]
        assert primary_is_equal(orig, back)


def test_io():
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

    with tempfile.TemporaryDirectory(prefix="test_primary_") as tmp_dir:
        path = os.path.join(tmp_dir, "steering.tar")
        cpw.steering.write_steerings(runs=orig, path=path)
        back = cpw.steering.read_steerings(path=path)

    for run_id in orig:
        assert orig[run_id]["run"] == back[run_id]["run"]
        assert orig[run_id]["primaries"] == back[run_id]["primaries"]
