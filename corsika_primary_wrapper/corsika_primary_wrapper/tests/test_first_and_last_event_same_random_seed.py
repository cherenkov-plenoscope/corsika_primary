import pytest
import os
import tempfile
import corsika_primary_wrapper as cpw
import corsika_wrapper as cw
import numpy as np

i4 = np.int32
i8 = np.int64
f8 = np.float64

@pytest.fixture()
def corsika_primary_path(pytestconfig):
    return pytestconfig.getoption("corsika_primary_path")


def test_same_random_seed_yields_same_event(corsika_primary_path):
    assert os.path.exists(corsika_primary_path)
    steering_dict = {
        "run": {
            "run_id": i8(1),
            "event_id_of_first_event": i8(1),
            "observation_level_asl_m": f8(2300),
            "earth_magnetic_field_x_muT": f8(12.5),
            "earth_magnetic_field_z_muT": f8(-25.9),
            "atmosphere_id": i8(10),
            "energy_range": {"start_GeV": f8(1.0), "stop_GeV": f8(5.0)},
        },
        "primaries": [
            {
                "particle_id": f8(1),
                "energy_GeV": f8(1.337),
                "zenith_rad": f8(0.0),
                "azimuth_rad": f8(0.0),
                "depth_g_per_cm2": f8(1.0),
                "random_seed": cpw.steering.make_simple_seed(42),
            },
            {
                "particle_id": f8(3),
                "energy_GeV": f8(4.32),
                "zenith_rad": f8(0.2),
                "azimuth_rad": f8(0.3),
                "depth_g_per_cm2": f8(34.0),
                "random_seed": cpw.steering.make_simple_seed(18),
            },
        ],
    }
    steering_dict["primaries"].append(steering_dict["primaries"][0].copy())

    with tempfile.TemporaryDirectory(prefix="test_primary_") as tmp_dir:
        run_path = os.path.join(tmp_dir, "same_first_and_last_event.tar")
        cpw.corsika_primary(
            corsika_path=corsika_primary_path,
            steering_dict=steering_dict,
            output_path=run_path,
        )
        assert os.path.exists(run_path)
        run = cpw.Tario(run_path)
        first_evth, first_bunches = next(run)
        second_evth, second_bunches = next(run)
        third_evth, third_bunches = next(run)
        with pytest.raises(StopIteration):
            next(run)

        assert first_evth[0] == third_evth[0]
        assert first_evth[1] == 1  # event-number
        assert third_evth[1] == 3  # event-number
        np.testing.assert_array_equal(first_evth[2:], third_evth[2:])
        np.testing.assert_array_equal(first_bunches, third_bunches)

        assert np.any(np.not_equal(first_evth[2:], second_evth[2:]))

        if first_bunches.shape[0] == second_bunches.shape[0]:
            assert np.any(np.not_equal(first_bunches, second_bunches))
