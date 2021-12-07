import pytest
import os
import corsika_primary as cpw
import inspect
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


def test_same_random_seed_yields_same_event(corsika_primary_path, debug_dir):
    tmp = cpw.testing.TmpDebugDir(
        debug_dir=debug_dir,
        suffix=inspect.getframeinfo(inspect.currentframe()).function,
    )

    energy_GeV = 7.0

    for particle_id in [1, 3, 14]:
        steering_dict = {
            "run": {
                "run_id": i8(1),
                "event_id_of_first_event": i8(1),
                "observation_level_asl_m": f8(2300),
                "earth_magnetic_field_x_muT": f8(12.5),
                "earth_magnetic_field_z_muT": f8(-25.9),
                "atmosphere_id": i8(10),
                "energy_range": {
                    "start_GeV": f8(energy_GeV * 0.9),
                    "stop_GeV": f8(energy_GeV * 1.1),
                },
            },
            "primaries": [],
        }

        same_primary = {
            "particle_id": f8(particle_id),
            "energy_GeV": f8(energy_GeV),
            "zenith_rad": f8(0.0),
            "azimuth_rad": f8(0.0),
            "depth_g_per_cm2": f8(0.0),
            "random_seed": cpw.random.seed.make_simple_seed(18),
        }

        num_primaries = 12
        for idx_primary in range(num_primaries):
            steering_dict["primaries"].append(same_primary.copy())

        run_path = os.path.join(tmp.name, "run_with_same_events.tar")
        if not os.path.exists(run_path):
            cpw.corsika_primary(
                corsika_path=corsika_primary_path,
                steering_dict=steering_dict,
                output_path=run_path,
            )
        run = cpw.tario.EventTapeReader(run_path)
        first_event = next(run)
        first_evth, first_bunches = first_event
        for event_idx, event in enumerate(run):
            evth, bunches = event
            assert first_evth[0] == evth[0]
            assert first_evth[1] != evth[1]  # event-number
            np.testing.assert_array_equal(first_evth[2:], evth[2:])
            np.testing.assert_array_equal(first_bunches, bunches)
        assert event_idx + 2 == num_primaries

    tmp.cleanup_when_no_debug()
