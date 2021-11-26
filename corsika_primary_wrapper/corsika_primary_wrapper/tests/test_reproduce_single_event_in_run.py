import pytest
import os
import tempfile
import corsika_primary_wrapper as cpw
import numpy as np
import hashlib
import json
import pprint


@pytest.fixture()
def corsika_primary_path(pytestconfig):
    return pytestconfig.getoption("corsika_primary_path")


@pytest.fixture()
def non_temporary_path(pytestconfig):
    return pytestconfig.getoption("non_temporary_path")


def make_explicit_steering(
    run_id, particle_id, num_primaries, energy_GeV, prng
):
    seed_maker_and_checker = cpw.random_seed.CorsikaRandomSeed(
        NUM_DIGITS_RUN_ID=4, NUM_DIGITS_AIRSHOWER_ID=5,
    )

    steering_dict = {
        "run": {
            "run_id": run_id,
            "event_id_of_first_event": 1,
            "observation_level_asl_m": 2300,
            "earth_magnetic_field_x_muT": 12.5,
            "earth_magnetic_field_z_muT": -25.9,
            "atmosphere_id": 10,
        },
        "primaries": [],
    }
    for airshower_id in np.arange(1, num_primaries + 1):
        az, zd = cpw.random_distributions.draw_azimuth_zenith_in_viewcone(
            prng=prng,
            azimuth_rad=np.deg2rad(20.0),
            zenith_rad=np.deg2rad(5.0),
            min_scatter_opening_angle_rad=np.deg2rad(0.0),
            max_scatter_opening_angle_rad=np.deg2rad(5.0),
            max_iterations=1000,
        )
        prm = {
            "particle_id": particle_id,
            "energy_GeV": energy_GeV,
            "zenith_rad": zd,
            "azimuth_rad": az,
            "depth_g_per_cm2": 0.0,
            "random_seed": cpw.simple_seed(
                seed=seed_maker_and_checker.random_seed_based_on(
                    run_id=run_id, airshower_id=airshower_id,
                ),
            ),
        }
        steering_dict["primaries"].append(prm)
    return steering_dict


def make_run_of_events_and_cherry_pick_events_to_be_reproduced(
    corsika_primary_path, steering_dict, events_to_be_reproduced, tmp_dir,
):
    os.makedirs(tmp_dir, exist_ok=True)

    run_path = os.path.join(tmp_dir, "complete_run.tar")
    pool_hashes_path = run_path + ".hashes.json"

    if not os.path.exists(pool_hashes_path):
        print("Create Cherenkov-pools and estimate their md5-hashes.")

        run = cpw.CorsikaPrimary(
            corsika_path=corsika_primary_path,
            steering_dict=steering_dict,
            stdout_path=run_path + ".o",
            stderr_path=run_path + ".e",
            tmp_dir_prefix="corsika_primary_",
        )

        cpw.steering_io.write_explicit_steerings(
            explicit_steerings={
                steering_dict["run"]["run_id"]: {
                    "steering_card": str(run.steering_card),
                    "primary_bytes": bytes(run.primary_bytes),
                }
            },
            path=run_path + ".steering.tar",
        )

        continous_pool_hashes = {}
        for event_idx, event in enumerate(run):
            evth, bunches = event
            h = hashlib.md5(bunches.tobytes()).hexdigest()
            print("Cherenkov_pool_hash", h)
            continous_pool_hashes[event_idx] = h

        with open(pool_hashes_path, "wt") as f:
            f.write(json.dumps(continous_pool_hashes, indent=4))

    with open(pool_hashes_path, "rt") as f:
        _tmp = json.loads(f.read())
        continous_pool_hashes = {}
        for key in _tmp:
            continous_pool_hashes[int(key)] = _tmp[key]

    explicit_steering = cpw.steering_io.read_explicit_steerings(
        path=run_path + ".steering.tar",
    )[steering_dict["run"]["run_id"]]

    reproduced_pool_hashes_path = os.path.join(
        tmp_dir, "reproduced_pool_hashes.json"
    )
    reproduced_pool_hashes = {}
    print("Reproduce single Cherenkov-pools and estimate their md5-hashes.")

    for event_idx in events_to_be_reproduced:
        steering_card = str(explicit_steering["steering_card"])
        primary_bytes = cpw._primaries_slice(
            primary_bytes=explicit_steering["primary_bytes"], i=event_idx
        )
        part_path = os.path.join(
            tmp_dir, "part_run_{:06d}.tar".format(event_idx)
        )

        if not os.path.exists(part_path):
            print("Create new: ", part_path)
            cpw.explicit_corsika_primary(
                corsika_path=corsika_primary_path,
                steering_card=steering_card,
                primary_bytes=primary_bytes,
                output_path=part_path,
                stdout_postfix=".o",
                stderr_postfix=".e",
                tmp_dir_prefix="corsika_primary_",
            )
        part_run = cpw.Tario(path=part_path)
        evth, bunches = next(part_run)
        h = hashlib.md5(bunches.tobytes()).hexdigest()
        reproduced_pool_hashes[event_idx] = h

    with open(reproduced_pool_hashes_path, "wt") as f:
        f.write(json.dumps(reproduced_pool_hashes, indent=4))

    return continous_pool_hashes, reproduced_pool_hashes


def all_cherenkov_pool_hashes_are_equal(
    original_hashes, reproduced_hashes, original_steering_dict
):
    all_identical = True
    for event_idx in reproduced_hashes:
        original = original_hashes[event_idx]
        reproduced = reproduced_hashes[event_idx]
        if reproduced != original:
            print("event_idx {: 6d} --- BAD ---".format(event_idx))
            print("pool-md5-hash original  : ", original)
            print("pool-md5-hash reproduced: ", reproduced)
            print("steering: ")
            pprint.pprint(original_steering_dict["primaries"][event_idx])
            all_identical = False
    return all_identical


def test_few_events_different_particles_reproduce_one(
    corsika_primary_path, non_temporary_path
):
    tmp_dir_handle = tempfile.TemporaryDirectory(prefix="corsika_primary_")
    tmp_dir = non_temporary_path if non_temporary_path else tmp_dir_handle.name

    assert os.path.exists(corsika_primary_path)
    prng = np.random.Generator(np.random.PCG64(42))

    NUM_PRIMARIES = 5
    EVENT_NUMBER = 3  # [1, 2, >3<, 4, 5]

    particles = {
        "gamma": {"particle_id": 1, "energy_GeV": 1.0},
        "electron": {"particle_id": 3, "energy_GeV": 1.0},
        "proton": {"particle_id": 14, "energy_GeV": 7},
        "helium": {"particle_id": 402, "energy_GeV": 12},
    }

    for pkey in particles:

        print(pkey, particles[pkey])

        complete_steering = make_explicit_steering(
            particle_id=particles[pkey]["particle_id"],
            run_id=6085,
            num_primaries=NUM_PRIMARIES,
            energy_GeV=particles[pkey]["energy_GeV"],
            prng=prng,
        )

        (
            original_hashes,
            reproduced_hashes,
        ) = make_run_of_events_and_cherry_pick_events_to_be_reproduced(
            corsika_primary_path=corsika_primary_path,
            steering_dict=complete_steering,
            events_to_be_reproduced=[3],
            tmp_dir=os.path.join(
                tmp_dir, "few_events_different_particles_reproduce_one", pkey,
            ),
        )

        particles[pkey]["reproduction"] = all_cherenkov_pool_hashes_are_equal(
            original_hashes=original_hashes,
            reproduced_hashes=reproduced_hashes,
            original_steering_dict=complete_steering,
        )

    all_particles_can_be_reproduced = True
    for pkey in particles:
        if particles[pkey]["reproduction"] == False:
            all_particles_can_be_reproduced = False

    assert all_particles_can_be_reproduced
    tmp_dir_handle.cleanup()


def test_many_helium_events_and_reproduce_all(
    corsika_primary_path, non_temporary_path
):
    """
    Motivation: In the magnetic deflection estimate I found some events ~50%
    which could not be reproduced i.e. did not yield the same Cherenkov-pool.
    """
    tmp_dir_handle = tempfile.TemporaryDirectory(prefix="corsika_primary_")
    tmp_dir = non_temporary_path if non_temporary_path else tmp_dir_handle.name

    prng = np.random.Generator(np.random.PCG64(42))

    particle_id = 402
    energy_GeV = 16.0
    num_events = int(800 / energy_GeV)
    events_to_be_reproduced = np.arange(num_events).tolist()

    original_steering_dict = make_explicit_steering(
        particle_id=particle_id,
        run_id=8189,
        num_primaries=num_events,
        energy_GeV=energy_GeV,
        prng=prng,
    )

    (
        original_hashes,
        reproduced_hashes,
    ) = make_run_of_events_and_cherry_pick_events_to_be_reproduced(
        corsika_primary_path=corsika_primary_path,
        steering_dict=original_steering_dict,
        events_to_be_reproduced=events_to_be_reproduced,
        tmp_dir=os.path.join(tmp_dir, "many_helium_events_and_reproduce_all"),
    )

    assert all_cherenkov_pool_hashes_are_equal(
        original_hashes=original_hashes,
        reproduced_hashes=reproduced_hashes,
        original_steering_dict=original_steering_dict,
    )
    tmp_dir_handle.cleanup()
