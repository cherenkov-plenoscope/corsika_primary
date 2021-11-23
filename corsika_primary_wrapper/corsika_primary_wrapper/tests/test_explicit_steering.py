import corsika_primary_wrapper as cpw
import numpy as np
import tempfile
import os


def make_dummy_primaries(num, prng):
    primaries = []
    for i in range(num):
        prm = {}
        prm["particle_id"] = int(prng.uniform(100))
        prm["energy_GeV"] = 1 + prng.uniform(5)
        prm["zenith_rad"] = prng.uniform(1)
        prm["azimuth_rad"] = prng.uniform(2) - 1
        prm["depth_g_per_cm2"] = 0.0
        prm["random_seed"] = []
        for j in range(4):
            seeds = {
                "SEED": int(prng.uniform(100)),
                "CALLS": int(prng.uniform(100)),
                "BILLIONS": int(prng.uniform(100)),
            }
            prm["random_seed"].append(seeds)
        primaries.append(prm)
    return primaries


def primary_is_equal(a, b):
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


STEERING_CARD_TEMPLATE = "SOMETHING JADADA\nRUNNR {:d}\nFOO BAR\nEXIT\n"


def test_primaries_dict_to_bytes_to_dict():
    prng = np.random.Generator(np.random.PCG64(42))
    NUM = 1337
    primaries_orig = make_dummy_primaries(num=NUM, prng=prng)
    primary_bytes = cpw._primaries_to_bytes(primaries=primaries_orig)
    primaries_back = cpw._primaries_to_dict(primary_bytes=primary_bytes)
    for i in range(NUM):
        orig = primaries_orig[i]
        back = primaries_back[i]
        assert primary_is_equal(orig, back)


def test_primary_bytes_extract_slice():
    prng = np.random.Generator(np.random.PCG64(402))
    NUM = 1337
    primaries_orig = make_dummy_primaries(num=NUM, prng=prng)
    primary_bytes = cpw._primaries_to_bytes(primaries=primaries_orig)
    for i in range(NUM):
        prm_pytes = cpw._primaries_slice(primary_bytes=primary_bytes, i=i)
        prm_back = cpw._primaries_to_dict(primary_bytes=prm_pytes)
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
        primaries = make_dummy_primaries(num=NUM_EVENTS, prng=prng)
        explicit_steering = {}
        explicit_steering["steering_card"] = STEERING_CARD_TEMPLATE.format(
            run_id
        )
        explicit_steering["primary_bytes"] = cpw._primaries_to_bytes(
            primaries=primaries
        )
        orig[run_id] = explicit_steering

    with tempfile.TemporaryDirectory(prefix="test_primary_") as tmp_dir:
        path = os.path.join(tmp_dir, "steering.tar")
        cpw.steering_io.write_explicit_steerings(
            explicit_steerings=orig, path=path
        )
        back = cpw.steering_io.read_explicit_steerings(path=path)

    for run_id in orig:
        assert orig[run_id]["steering_card"] == back[run_id]["steering_card"]
        assert orig[run_id]["primary_bytes"] == back[run_id]["primary_bytes"]
