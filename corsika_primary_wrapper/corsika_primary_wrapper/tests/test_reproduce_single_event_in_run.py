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


def hash_cherenkov_pools(
    corsika_primary_path,
    steering_card,
    primary_bytes,
    tmp_key,
    tmp_dir,
):
    os.makedirs(tmp_dir, exist_ok=True)

    path = os.path.join(tmp_dir, tmp_key)
    hashes_path = path + ".hashes.csv"

    if not os.path.exists(hashes_path):
        run = cpw.CorsikaPrimary(
            corsika_path=corsika_primary_path,
            steering_card=steering_card,
            primary_bytes=primary_bytes,
            stdout_path=path + ".o",
            stderr_path=path + ".e",
            tmp_dir_prefix="corsika_primary_",
        )

        hashes_csv = ""
        for event in run:
            evth, bunches = event
            event_id = int(evth[cpw.I_EVTH_EVENT_NUMBER])
            h = hashlib.md5(bunches.tobytes()).hexdigest()
            _csv_line = "{:06d},{:s}".format(event_id, h)
            hashes_csv += _csv_line + "\n"

        with open(hashes_path, "wt") as f:
            f.write(hashes_csv)

    with open(hashes_path, "rt") as f:
        hashes = {}
        for line in str.splitlines(f.read()):
            event_id_str, h_str = str.split(line, ",")
            hashes[int(event_id_str)] = h_str

    return hashes



def make_run_and_cherry_pick_event_ids_to_reproduce(
    corsika_primary_path,
    explicit_steerings,
    event_ids_to_reproduce,
    tmp_dir,
):
    assert os.path.exists(corsika_primary_path)
    run_ids = list(explicit_steerings.keys())
    assert len(run_ids) == 1
    run_id = run_ids[0]

    os.makedirs(tmp_dir, exist_ok=True)

    complete_hashes = hash_cherenkov_pools(
        corsika_primary_path=corsika_primary_path,
        steering_card=explicit_steerings[run_id]["steering_card"],
        primary_bytes=explicit_steerings[run_id]["primary_bytes"],
        tmp_key="complete",
        tmp_dir=tmp_dir,
    )

    part_hashes = {}
    for event_ids in event_ids_to_reproduce:

        primary_bytes_for_idx = cpw._primaries_slice(
            primary_bytes=explicit_steerings[run_id]["primary_bytes"],
            i=(event_ids - 1)
        )
        part_hash = hash_cherenkov_pools(
            corsika_primary_path=corsika_primary_path,
            steering_card=explicit_steerings[run_id]["steering_card"],
            primary_bytes=primary_bytes_for_idx,
            tmp_key="part_{:06d}".format(event_ids),
            tmp_dir=tmp_dir,
        )
        part_hashes[event_ids] = part_hash[1]

    return complete_hashes, part_hashes


def all_cherenkov_pool_hashes_are_equal(
    original_hashes, reproduced_hashes, original_steering_dict
):
    all_identical = True
    for event_id in reproduced_hashes:
        original = original_hashes[event_id]
        reproduced = reproduced_hashes[event_id]
        if reproduced != original:
            print("event_id {: 6d} --- BAD ---".format(event_id))
            print("pool-md5-hash original  : ", original)
            print("pool-md5-hash reproduced: ", reproduced)
            print("steering: ")
            pprint.pprint(original_steering_dict["primaries"][event_id])
            all_identical = False
    return all_identical


PARTICLES = {
    "gamma": {"particle_id": 1, "energy_GeV": 1.0},
    "electron": {"particle_id": 3, "energy_GeV": 1.0},
    "proton": {"particle_id": 14, "energy_GeV": 7},
    "helium": {"particle_id": 402, "energy_GeV": 12},
}


def test_few_events_different_particles_reproduce_one(
    corsika_primary_path, non_temporary_path
):
    tmp_dir_handle = tempfile.TemporaryDirectory(prefix="corsika_primary_")
    tmp_dir = non_temporary_path if non_temporary_path else tmp_dir_handle.name

    assert os.path.exists(corsika_primary_path)
    prng = np.random.Generator(np.random.PCG64(42))

    num_primaries = 15

    reproduction = {}
    for pkey in PARTICLES:
        steering_dict = make_explicit_steering(
            particle_id=PARTICLES[pkey]["particle_id"],
            run_id=6085,
            num_primaries=num_primaries,
            energy_GeV=PARTICLES[pkey]["energy_GeV"],
            prng=prng,
        )

        (
            original_hashes,
            reproduced_hashes,
        ) = make_run_and_cherry_pick_event_ids_to_reproduce(
            corsika_primary_path=corsika_primary_path,
            explicit_steerings=cpw.steering_dict_to_explicit_steerings(
                steering_dict=steering_dict
            ),
            event_ids_to_reproduce=[4,7,13],
            tmp_dir=os.path.join(
                tmp_dir, "few_events_different_particles_reproduce_one", pkey,
            ),
        )

        reproduction[pkey] = all_cherenkov_pool_hashes_are_equal(
            original_hashes=original_hashes,
            reproduced_hashes=reproduced_hashes,
            original_steering_dict=steering_dict,
        )

    all_particles_can_be_reproduced = True
    for pkey in PARTICLES:
        if reproduction[pkey] == False:
            all_particles_can_be_reproduced = False

    assert all_particles_can_be_reproduced
    tmp_dir_handle.cleanup()


def test_reproduce_full_run(
    corsika_primary_path, non_temporary_path
):
    """
    Motivation: In the magnetic deflection estimate I found some events ~50%
    which could not be reproduced i.e. did not yield the same Cherenkov-pool.
    Here we test if it yields at lest the same result when it is called
    multiple times with same input.
    """

    tmp_dir_handle = tempfile.TemporaryDirectory(prefix="corsika_primary_")
    tmp_dir = non_temporary_path if non_temporary_path else tmp_dir_handle.name

    prng = np.random.Generator(np.random.PCG64(42))
    num_iterations = 5

    multiplicity = {}
    for pkey in PARTICLES:
        num_events = int(500 / PARTICLES[pkey]["energy_GeV"])

        steering_dict = make_explicit_steering(
            particle_id=PARTICLES[pkey]["particle_id"],
            run_id=8189,
            num_primaries=num_events,
            energy_GeV=PARTICLES[pkey]["energy_GeV"],
            prng=prng,
        )

        steering_card, primary_bytes = cpw._dict_to_card_and_bytes(
            steering_dict=steering_dict
        )

        M = []
        for i in range(num_iterations):
            hashes = hash_cherenkov_pools(
                corsika_primary_path=corsika_primary_path,
                steering_card=steering_card,
                primary_bytes=primary_bytes,
                tmp_key="{:06d}".format(i),
                tmp_dir=os.path.join(
                    tmp_dir,
                    "test_reproduce_full_run",
                    pkey,
                ),
            )
            M.append(hashes)

        multiplicity[pkey] = {}
        for event_id in np.arange(1, num_events + 1):
            list_of_hashes_in_iterations = [
                M[i][event_id] for i in range(num_iterations)
            ]
            multiplicity[pkey][event_id] = len(set(
                list_of_hashes_in_iterations
            ))

    all_iterations_yield_same_cherenkov_pool = True
    for pkey in PARTICLES:
        for event_id in multiplicity[pkey]:
            num_different_cherenkov_pools = multiplicity[pkey][event_id]
            if num_different_cherenkov_pools > 1:
                all_iterations_yield_same_cherenkov_pool = False
                print(
                    pkey,
                    "event_id",
                    event_id,
                    "num_different_cherenkov_pools",
                    num_different_cherenkov_pools
                )

    assert all_iterations_yield_same_cherenkov_pool

    tmp_dir_handle.cleanup()
