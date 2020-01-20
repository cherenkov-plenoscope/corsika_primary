import pytest
import os
import tempfile
import corsika_primary_wrapper as cpw
import corsika_wrapper as cw
import numpy as np


@pytest.fixture()
def corsika_primary_path(pytestconfig):
    return pytestconfig.getoption("corsika_primary_path")


def test_same_random_seed_yields_same_event(corsika_primary_path):
    assert(os.path.exists(corsika_primary_path))
    steering_dict = {
        "run": {
            "run_id": 1,
            "event_id_of_first_event": 1,
            "observation_level_asl_m": 2300,
            "earth_magnetic_field_x_muT": 12.5,
            "earth_magnetic_field_z_muT": -25.9,
            "atmosphere_id": 10,
        },
        "primaries": [
            {
                "particle_id": 1,
                "energy_GeV": 1.337,
                "zenith_rad": 0.0,
                "azimuth_rad": 0.0,
                "depth_g_per_cm2": 1.0,
                "random_seed": cpw._simple_seed(42),
            },
            {
                "particle_id": 3,
                "energy_GeV": 4.32,
                "zenith_rad": 0.2,
                "azimuth_rad": 0.3,
                "depth_g_per_cm2": 34.0,
                "random_seed": cpw._simple_seed(18),
            },
        ]
    }
    steering_dict["primaries"].append(steering_dict["primaries"][0].copy())

    with tempfile.TemporaryDirectory(prefix="test_primary_") as tmp_dir:
        run_path = os.path.join(tmp_dir, "same_first_and_last_event.tar")
        cpw.corsika_primary(
            corsika_path=corsika_primary_path,
            steering_dict=steering_dict,
            output_path=run_path)
        assert(os.path.exists(run_path))
        run = cpw.Tario(run_path)
        first_evth, first_bunches = next(run)
        second_evth, second_bunches = next(run)
        third_evth, third_bunches = next(run)
        with pytest.raises(StopIteration):
            next(run)

        assert(first_evth[0] == third_evth[0])
        assert(first_evth[1] == 1)  # event-number
        assert(third_evth[1] == 3)  # event-number
        np.testing.assert_array_equal(first_evth[2:], third_evth[2:])
        np.testing.assert_array_equal(first_bunches, third_bunches)

        assert np.any(np.not_equal(first_evth[2:], second_evth[2:]))

        if first_bunches.shape[0] == second_bunches.shape[0]:
            assert np.any(np.not_equal(first_bunches, second_bunches))
