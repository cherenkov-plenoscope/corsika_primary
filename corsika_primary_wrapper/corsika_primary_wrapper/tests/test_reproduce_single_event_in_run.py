import pytest
import os
import tempfile
import corsika_primary_wrapper as cpw
import numpy as np
import hashlib
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


def make_run_of_events_and_cherry_pick_event_idx_to_reproduce(
    corsika_primary_path,
    explicit_steerings,
    event_idx_to_reproduce,
    tmp_dir,
):
    assert os.path.exists(corsika_primary_path)
    run_ids = list(explicit_steerings.keys())
    assert len(run_ids) == 1
    run_id = run_ids[0]

    os.makedirs(tmp_dir, exist_ok=True)

    complete_path = os.path.join(tmp_dir, "complete")
    complete_hashes_path = complete_path + ".hashes.csv"

    if not os.path.exists(complete_hashes_path):
        print("Create Cherenkov-pools and estimate their md5-hashes.")

        run = cpw.CorsikaPrimary(
            corsika_path=corsika_primary_path,
            steering_card=explicit_steerings[run_id]["steering_card"],
            primary_bytes=explicit_steerings[run_id]["primary_bytes"],
            stdout_path=complete_path + ".o",
            stderr_path=complete_path + ".e",
            tmp_dir_prefix="corsika_primary_",
        )

        complete_hashes_csv = ""
        for event_idx, event in enumerate(run):
            evth, bunches = event
            h = hashlib.md5(bunches.tobytes()).hexdigest()
            _csv_line = "{:06d},{:s}\n".format(event_idx, h)
            print(_csv_line)
            complete_hashes_csv += _csv_line

        with open(complete_hashes_path, "wt") as f:
            f.write(complete_hashes_csv)

    with open(complete_hashes_path, "rt") as f:
        complete_hashes = {}
        for line in str.splitlines(f.read()):
            idx_str, h_str = str.split(line, ",")
            complete_hashes[int(idx_str)] = h_str


    print("Reproduce single Cherenkov-pools and estimate their md5-hashes.")
    part_hashes = {}
    for event_idx in event_idx_to_reproduce:
        primary_bytes_for_idx = cpw._primaries_slice(
            primary_bytes=explicit_steerings[run_id]["primary_bytes"],
            i=event_idx
        )
        part_idx_path = os.path.join(tmp_dir, "part_{:06d}".format(event_idx))
        part_idx_hash_path = part_idx_path + ".hash.csv"

        if not os.path.exists(part_idx_hash_path):
            print("Create new: ", event_idx)

            part_run = cpw.CorsikaPrimary(
                corsika_path=corsika_primary_path,
                steering_card=explicit_steerings[run_id]["steering_card"],
                primary_bytes=primary_bytes_for_idx,
                stdout_path=part_idx_path + ".o",
                stderr_path=part_idx_path + ".e",
                tmp_dir_prefix="corsika_primary_",
            )

            evth, bunches = next(part_run)
            h = hashlib.md5(bunches.tobytes()).hexdigest()
            with open(part_idx_hash_path, "wt") as f:
                f.write("{:06d},{:s}\n".format(event_idx, h))

        with open(part_idx_hash_path, "rt") as f:
            for line in str.splitlines(f.read()):
                idx_str, h_str = str.split(line, ",")
                part_hashes[int(idx_str)] = h_str

    return complete_hashes, part_hashes


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

        steering_dict = make_explicit_steering(
            particle_id=particles[pkey]["particle_id"],
            run_id=6085,
            num_primaries=NUM_PRIMARIES,
            energy_GeV=particles[pkey]["energy_GeV"],
            prng=prng,
        )

        (
            original_hashes,
            reproduced_hashes,
        ) = make_run_of_events_and_cherry_pick_event_idx_to_reproduce(
            corsika_primary_path=corsika_primary_path,
            explicit_steerings=cpw.steering_dict_to_explicit_steerings(
                steering_dict=steering_dict
            ),
            event_idx_to_reproduce=[3],
            tmp_dir=os.path.join(
                tmp_dir, "few_events_different_particles_reproduce_one", pkey,
            ),
        )

        particles[pkey]["reproduction"] = all_cherenkov_pool_hashes_are_equal(
            original_hashes=original_hashes,
            reproduced_hashes=reproduced_hashes,
            original_steering_dict=steering_dict,
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
    event_idx_to_reproduce = np.arange(num_events).tolist()

    steering_dict = make_explicit_steering(
        particle_id=particle_id,
        run_id=8189,
        num_primaries=num_events,
        energy_GeV=energy_GeV,
        prng=prng,
    )

    (
        original_hashes,
        reproduced_hashes,
    ) = make_run_of_events_and_cherry_pick_event_idx_to_reproduce(
        corsika_primary_path=corsika_primary_path,
        explicit_steerings=cpw.steering_dict_to_explicit_steerings(
            steering_dict=steering_dict
        ),
        event_idx_to_reproduce=event_idx_to_reproduce,
        tmp_dir=os.path.join(tmp_dir, "many_helium_events_and_reproduce_all"),
    )

    assert all_cherenkov_pool_hashes_are_equal(
        original_hashes=original_hashes,
        reproduced_hashes=reproduced_hashes,
        original_steering_dict=steering_dict,
    )
    tmp_dir_handle.cleanup()
