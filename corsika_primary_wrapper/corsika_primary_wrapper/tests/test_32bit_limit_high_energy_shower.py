import pytest
import os
import tempfile
import corsika_primary_wrapper as cpw
import corsika_wrapper as cw
import numpy as np


@pytest.fixture()
def corsika_primary_path(pytestconfig):
    return pytestconfig.getoption("corsika_primary_path")


@pytest.fixture()
def non_temporary_path(pytestconfig):
    return pytestconfig.getoption("non_temporary_path")


def test_no_obvious_32bit_limitations(
    corsika_primary_path,
    non_temporary_path
):
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
                "particle_id": 3,
                "energy_GeV": 3.3e3,
                "zenith_rad": 0.0,
                "azimuth_rad": 0.0,
                "depth_g_per_cm2": 0.0,
                "random_seed": cpw._simple_seed(0),
            }
        ]
    }

    tmp_prefix = "test_32bit_limit_high_energy_shower"
    with tempfile.TemporaryDirectory(prefix=tmp_prefix) as tmp_dir:
        if non_temporary_path != "":
            tmp_dir = os.path.join(non_temporary_path, tmp_prefix)
            os.makedirs(tmp_dir, exist_ok=True)

        run_path = os.path.join(tmp_dir, "high_energy_electron.tar")
        if not os.path.exists(run_path):
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

        sufficient_bunches = int(5e9//cpw.NUM_BYTES_PER_BUNCH)

        assert bunches.shape[0] > sufficient_bunches
