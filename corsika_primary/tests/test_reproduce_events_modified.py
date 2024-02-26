import pytest
import os
import corsika_primary as cpw
import inspect
import numpy as np
import hashlib
import pprint
import copy

i4 = np.int32
i8 = np.int64
f8 = np.float64


@pytest.fixture()
def corsika_primary_path(pytestconfig):
    return pytestconfig.getoption("corsika_primary_path")


@pytest.fixture()
def debug_dir(pytestconfig):
    return pytestconfig.getoption("debug_dir")


def make_random_steering_dict(
    run_id, particle_id, num_primaries, energy_GeV, prng
):
    steering_dict = {
        "run": {
            "run_id": i8(run_id),
            "event_id_of_first_event": i8(1),
            "observation_level_asl_m": f8(2300),
            "earth_magnetic_field_x_muT": f8(12.5),
            "earth_magnetic_field_z_muT": f8(-25.9),
            "atmosphere_id": i8(10),
            "energy_range": {
                "start_GeV": f8(energy_GeV),
                "stop_GeV": f8(energy_GeV),
            },
            "random_seed": cpw.random.seed.make_simple_seed(seed=run_id),
        },
        "primaries": [],
    }
    for event_id in np.arange(1, num_primaries + 1):
        az, zd = cpw.random.distributions.draw_azimuth_zenith_in_viewcone(
            prng=prng,
            azimuth_rad=np.deg2rad(20.0),
            zenith_rad=np.deg2rad(5.0),
            min_scatter_opening_angle_rad=np.deg2rad(0.0),
            max_scatter_opening_angle_rad=np.deg2rad(5.0),
            max_iterations=1000,
        )
        prm = {
            "particle_id": f8(particle_id),
            "energy_GeV": f8(energy_GeV),
            "theta_rad": f8(zd),
            "phi_rad": f8(az),
            "depth_g_per_cm2": f8(0.0),
        }
        steering_dict["primaries"].append(prm)
    return steering_dict


def hash_cherenkov_pools(
    corsika_primary_path,
    steering_dict,
    tmp_key,
    tmp_dir,
):
    os.makedirs(tmp_dir, exist_ok=True)
    run_path = os.path.join(tmp_dir, tmp_key)
    par_path = run_path + ".par.dat"
    hashes_path = run_path + ".hashes.csv"
    seeds_path = run_path + ".seeds.csv"

    hashes = {}
    seeds = {}

    if not os.path.exists(hashes_path):
        with cpw.CorsikaPrimary(
            corsika_path=corsika_primary_path,
            steering_dict=steering_dict,
            particle_output_path=par_path,
            stdout_path=run_path + ".o",
            stderr_path=run_path + ".e",
        ) as run:
            for event in run:
                evth, cer_reader = event

                cer_blocks = []
                for cer_block in cer_reader:
                    cer_blocks.append(cer_block)
                cer_blocks = np.vstack(cer_blocks)

                event_id = int(evth[cpw.I.EVTH.EVENT_NUMBER])
                hashes[event_id] = hashlib.md5(
                    cer_blocks.tobytes()
                ).hexdigest()
                seeds[event_id] = cpw.random.seed.parse_seed_from_evth(evth)

            cpw.testing.write_hashes(path=hashes_path, hashes=hashes)
            cpw.testing.write_seeds(path=seeds_path, seeds=seeds)

    hashes = cpw.testing.read_hashes(path=hashes_path)
    seeds = cpw.testing.read_seeds(path=seeds_path)

    return hashes, seeds


def make_run_and_cherry_pick_event_ids_to_reproduce(
    corsika_primary_path,
    steering_dict,
    event_ids_to_reproduce,
    tmp_dir,
):
    os.makedirs(tmp_dir, exist_ok=True)

    complete_hashes, complete_seeds = hash_cherenkov_pools(
        corsika_primary_path=corsika_primary_path,
        steering_dict=steering_dict,
        tmp_key="complete",
        tmp_dir=tmp_dir,
    )

    part_hashes = {}
    for event_id in event_ids_to_reproduce:
        event_idx = event_id - steering_dict["run"]["event_id_of_first_event"]

        part_steering_dict = {}
        part_steering_dict["run"] = copy.deepcopy(steering_dict["run"])
        part_steering_dict["run"]["random_seed"] = complete_seeds[event_id]
        part_steering_dict["primaries"] = []
        part_steering_dict["primaries"].append(
            copy.deepcopy(steering_dict["primaries"][event_idx])
        )

        part_hash, part_seed = hash_cherenkov_pools(
            corsika_primary_path=corsika_primary_path,
            steering_dict=part_steering_dict,
            tmp_key="part_{:06d}".format(event_id),
            tmp_dir=tmp_dir,
        )
        part_hashes[event_id] = part_hash[1]

    return complete_hashes, part_hashes


def cherenkov_pool_hashes_are_different(
    original_hashes, reproduced_hashes, original_steering_dict
):
    diff = []
    for event_id in reproduced_hashes:
        event_idx = (
            event_id - original_steering_dict["run"]["event_id_of_first_event"]
        )
        original = original_hashes[event_id]
        reproduced = reproduced_hashes[event_id]
        if reproduced != original:
            print("event_id {: 6d} --- BAD ---".format(event_id))
            print("pool-md5-hash original  : ", original)
            print("pool-md5-hash reproduced: ", reproduced)
            print("steering: ")
            pprint.pprint(original_steering_dict["primaries"][event_idx])
            diff.append(event_id)
    return set(diff)


PARTICLES = {
    "gamma": {
        "particle_id": 1,
        "energy_GeV": 1.0,
        "expected_to_fail": set([]),
    },
    "electron": {
        "particle_id": 3,
        "energy_GeV": 1.0,
        "expected_to_fail": set([]),
    },
    "proton": {
        "particle_id": 14,
        "energy_GeV": 7.0,
        "expected_to_fail": set([15]),
    },
    "helium": {
        "particle_id": 402,
        "energy_GeV": 12.0,
        "expected_to_fail": set([6, 7, 8, 13]),
    },
}


def test_few_events_different_particles_reproduce_one(
    corsika_primary_path, debug_dir
):
    tmp = cpw.testing.TmpDebugDir(
        debug_dir=debug_dir,
        suffix=inspect.getframeinfo(inspect.currentframe()).function,
    )

    prng = np.random.Generator(np.random.PCG64(42))

    num_primaries = 15
    event_ids_to_reproduce = np.arange(1, num_primaries + 1)

    failing_event_ids = {}
    for pkey in PARTICLES:
        steering_dict = make_random_steering_dict(
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
            steering_dict=steering_dict,
            event_ids_to_reproduce=event_ids_to_reproduce,
            tmp_dir=os.path.join(tmp.name, pkey),
        )

        failing_event_ids[pkey] = cherenkov_pool_hashes_are_different(
            original_hashes=original_hashes,
            reproduced_hashes=reproduced_hashes,
            original_steering_dict=steering_dict,
        )

    failing_is_as_expected = True
    for pkey in PARTICLES:
        if failing_event_ids[pkey] != PARTICLES[pkey]["expected_to_fail"]:
            print(pkey, "does not fail as expected.")

    tmp.cleanup_when_no_debug()


def test_reproduce_full_run(corsika_primary_path, debug_dir):
    """
    Motivation: In the magnetic deflection estimate I found some events ~50%
    which could not be reproduced i.e. did not yield the same Cherenkov-pool.
    Here we test if it yields at lest the same result when it is called
    multiple times with same input.
    """
    tmp = cpw.testing.TmpDebugDir(
        debug_dir=debug_dir,
        suffix=inspect.getframeinfo(inspect.currentframe()).function,
    )

    prng = np.random.Generator(np.random.PCG64(42))
    num_iterations = 5

    multiplicity = {}
    for pkey in PARTICLES:
        num_events = int(500 / PARTICLES[pkey]["energy_GeV"])

        steering_dict = make_random_steering_dict(
            particle_id=PARTICLES[pkey]["particle_id"],
            run_id=8189,
            num_primaries=num_events,
            energy_GeV=PARTICLES[pkey]["energy_GeV"],
            prng=prng,
        )

        M = []
        for i in range(num_iterations):
            hashes, seeds = hash_cherenkov_pools(
                corsika_primary_path=corsika_primary_path,
                steering_dict=steering_dict,
                tmp_key="{:06d}".format(i),
                tmp_dir=os.path.join(tmp.name, pkey),
            )
            M.append(hashes)

        multiplicity[pkey] = {}
        for event_id in np.arange(1, num_events + 1):
            list_of_hashes_in_iterations = [
                M[i][event_id] for i in range(num_iterations)
            ]
            multiplicity[pkey][event_id] = len(
                set(list_of_hashes_in_iterations)
            )

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
                    num_different_cherenkov_pools,
                )

    assert all_iterations_yield_same_cherenkov_pool

    tmp.cleanup_when_no_debug()
