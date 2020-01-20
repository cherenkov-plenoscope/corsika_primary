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

    for particle_id in [1, 3, 14]:
        steering_dict = {
            "run": {
                "run_id": 1,
                "event_id_of_first_event": 1,
                "observation_level_asl_m": 2300,
                "earth_magnetic_field_x_muT": 12.5,
                "earth_magnetic_field_z_muT": -25.9,
                "atmosphere_id": 10,
            },
            "primaries": []}

        same_primary = {
            "particle_id": particle_id,
            "energy_GeV": 7.0,
            "zenith_rad": 0.0,
            "azimuth_rad": 0.0,
            "depth_g_per_cm2": 0.0,
            "random_seed": cpw._simple_seed(0),
        }

        num_primaries = 12
        for idx_primary in range(num_primaries):
            steering_dict["primaries"].append(same_primary.copy())

        with tempfile.TemporaryDirectory(prefix="test_primary_") as tmp_dir:
            run_path = os.path.join(tmp_dir, "run_with_same_events.tar")
            cpw.corsika_primary(
                corsika_path=corsika_primary_path,
                steering_dict=steering_dict,
                output_path=run_path)
            run = cpw.Tario(run_path)
            first_event = next(run)
            first_evth, first_bunches = first_event
            for event_idx, event in enumerate(run):
                evth, bunches = event
                assert(first_evth[0] == evth[0])
                assert(first_evth[1] != evth[1])  # event-number
                np.testing.assert_array_equal(first_evth[2:], evth[2:])
                np.testing.assert_array_equal(first_bunches, bunches)
            assert(event_idx+2 == num_primaries)
