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
            "observation_level_altitude_asl": 2300,
            "earth_magnetic_field_x_muT": 12.5,
            "earth_magnetic_field_z_muT": -25.9,
            "atmosphere_id": 10,},
        "primaries": [
            {
                "particle_id": 3,
                "energy_GeV": 2.5e3,
                "zenith_rad": 0.0,
                "azimuth_rad": 0.0,
                "depth_g_per_cm2": 0.0,
                "random_seed": 0,
            }
        ]
    }

    with tempfile.TemporaryDirectory(prefix="test_primary_") as tmp_dir:
        run_path = os.path.join(tmp_dir, "high_energy_electron.tar")
        cpw.corsika_primary(
            corsika_path=corsika_primary_path,
            steering_dict=steering_dict,
            output_path=run_path)
        run = cpw.Tario(run_path)
        event = next(run)
        evth, bunches = event
        with pytest.raises(StopIteration):
            next(run)

        assert(cpw._evth_event_number(evth) == 1.)
        assert(cpw._evth_particle_id(evth) == 3.)
        assert(cpw._evth_starting_depth_g_per_cm2(evth) == 0.)

        sufficient_bunches = int(5e9//cpw.NUM_BYTES_PER_PRIMARY)

        assert bunches.shape[0] > sufficient_bunches

