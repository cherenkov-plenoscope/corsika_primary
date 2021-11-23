import pytest
import os
import tempfile
import corsika_primary_wrapper as cpw
import corsika_wrapper as cw
import numpy as np


@pytest.fixture()
def corsika_primary_path(pytestconfig):
    return pytestconfig.getoption("corsika_primary_path")


def make_explicit_steering(particle_id, seed, num_primaries, E_start):
    steering_dict = {
        "run": {
            "run_id": 1,
            "event_id_of_first_event": 1,
            "observation_level_asl_m": 2300,
            "earth_magnetic_field_x_muT": 12.5,
            "earth_magnetic_field_z_muT": -25.9,
            "atmosphere_id": 10,
        },
        "primaries": [],
    }
    for i in range(num_primaries):
        iseed = i + seed
        prm = {
            "particle_id": particle_id,
            "energy_GeV": E_start + float(iseed),
            "zenith_rad": np.deg2rad(iseed),
            "azimuth_rad": np.deg2rad(iseed),
            "depth_g_per_cm2": 0.0,
            "random_seed": cpw.simple_seed(iseed),
        }
        steering_dict["primaries"].append(prm)
    return steering_dict


I_EVTH_ENERGY_LOWER_LIMIT = 59
I_EVTH_ENERGY_UPPER_LIMIT = 60

def test_same_random_seed_yields_same_event(corsika_primary_path):
    assert os.path.exists(corsika_primary_path)
    NUM_PRIMARIES = 5
    EVENT_NUMBER = 3  # [1, 2, >3<, 4, 5]

    particles = {
        1: {"name": "gamma", "E_start": 1.0},
        3: {"name": "electron", "E_start": 1.0},
        14: {"name": "proton", "E_start": 7},
        402: {"name": "helium", "E_start": 12},
    }

    seed = 0
    for particle_id in particles:

        print(particles[particle_id])

        complete_steering = make_explicit_steering(
            particle_id=particle_id,
            seed=seed,
            num_primaries=NUM_PRIMARIES,
            E_start=particles[particle_id]["E_start"]
        )

        assert len(complete_steering["primaries"]) == NUM_PRIMARIES

        with tempfile.TemporaryDirectory(prefix="test_primary_") as tmp_dir:
            complete_run_path = os.path.join(tmp_dir, "complete_run.tar")

            cpw.corsika_primary(
                corsika_path=corsika_primary_path,
                steering_dict=complete_steering,
                output_path=complete_run_path,
            )

            # now reproduce event with event_id = 3, the middle one
            # -----------------------------------------------------

            part_run_path = os.path.join(tmp_dir, "part_run.tar")

            part_steering = {}
            part_steering["run"] = dict(complete_steering["run"])
            part_steering["run"]["event_id_of_first_event"] = 3
            part_steering["primaries"] = [
                complete_steering["primaries"][2]
            ]

            cpw.corsika_primary(
                corsika_path=corsika_primary_path,
                steering_dict=part_steering,
                output_path=part_run_path,
            )

            # read event 3 from complete_run
            # ------------------------------
            complete_run = cpw.Tario(complete_run_path)
            c_runh = complete_run.runh
            for i in range(3):
                c_evth, c_bunches = next(complete_run)


            # read reproduced event 3 from part_run
            # -------------------------------------
            part_run = cpw.Tario(part_run_path)
            p_runh = part_run.runh
            p_evth, p_bunches = next(part_run)

            # compare EVTHs, except energy range in run
            # -----------------------------------------
            for ii in range(273):
                if ii == I_EVTH_ENERGY_LOWER_LIMIT - 1:
                    pass
                elif ii == I_EVTH_ENERGY_UPPER_LIMIT - 1:
                    pass
                else:
                    assert c_evth[ii] == p_evth[ii], "[{:d}]".format(ii)

            # compare Cherenkov-pool
            # ----------------------
            np.testing.assert_array_equal(p_bunches, c_bunches)
