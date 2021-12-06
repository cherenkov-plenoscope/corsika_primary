import pytest
import inspect
import os
import tempfile
import corsika_primary as cpw
import numpy as np

i4 = np.int32
i8 = np.int64
f8 = np.float64


@pytest.fixture()
def corsika_primary_path(pytestconfig):
    return pytestconfig.getoption("corsika_primary_path")


@pytest.fixture()
def debug_dir(pytestconfig):
    return pytestconfig.getoption("debug_dir")


def test_32bit_limit_high_energy_shower(corsika_primary_path, debug_dir):
    tmp = cpw.testing.TmpDebugDir(
        debug_dir=debug_dir,
        suffix=inspect.getframeinfo(inspect.currentframe()).function,
    )

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
                "random_seed": cpw.random.seed.make_simple_seed(1),
            }
        ],
    }

    run_path = os.path.join(tmp.name, "high_energy_electron.tar")
    if not os.path.exists(run_path):
        cpw.corsika_primary(
            corsika_path=corsika_primary_path,
            steering_dict=steering_dict,
            output_path=run_path,
        )
    run = cpw.tario.Tario(run_path)
    event = next(run)
    evth, bunches = event
    with pytest.raises(StopIteration):
        next(run)

    assert evth[cpw.I.EVTH.EVENT_NUMBER] == 1.0
    assert evth[cpw.I.EVTH.PARTICLE_ID] == 3.0
    assert evth[cpw.I.EVTH.STARTING_DEPTH_G_PER_CM2] == 0.0

    sufficient_bunches = int(5e9 // cpw.I.BUNCH.NUM_BYTES)

    assert bunches.shape[0] > sufficient_bunches

    tmp.cleanup_when_no_debug()
