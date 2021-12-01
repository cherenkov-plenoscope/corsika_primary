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


@pytest.fixture()
def non_temporary_path(pytestconfig):
    return pytestconfig.getoption("non_temporary_path")


def test_no_obvious_32bit_limitations(
    corsika_primary_path, non_temporary_path
):
    assert os.path.exists(corsika_primary_path)
    steering_dict = {
        "run": {
            "run_id": i8(1),
            "event_id_of_first_event": i8(1),
            "observation_level_asl_m": f8(2300),
            "earth_magnetic_field_x_muT": f8(12.5),
            "earth_magnetic_field_z_muT": f8(-25.9),
            "atmosphere_id": i8(10),
            "energy_range": {"start_GeV": f8(3.2e3), "stop_GeV": f8(3.4e3)},
        },
        "primaries": [
            {
                "particle_id": f8(3),
                "energy_GeV": f8(3.3e3),
                "zenith_rad": f8(0.0),
                "azimuth_rad": f8(0.0),
                "depth_g_per_cm2": f8(0.0),
                "random_seed": cpw.random_seed.make_simple_seed(0),
            }
        ],
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
                output_path=run_path,
            )
        run = cpw.Tario(run_path)
        event = next(run)
        evth, bunches = event
        with pytest.raises(StopIteration):
            next(run)

        assert evth[cpw.I_EVTH_EVENT_NUMBER] == 1.0
        assert evth[cpw.I_EVTH_PARTICLE_ID] == 3.0
        assert evth[cpw.I_EVTH_STARTING_DEPTH_G_PER_CM2] == 0.0

        sufficient_bunches = int(5e9 // cpw.NUM_BYTES_PER_BUNCH)

        assert bunches.shape[0] > sufficient_bunches
