import pytest
import os
import tempfile
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


def test_different_starting_depths(corsika_primary_path, debug_dir):
    tmp = cpw.testing.TmpDebugDir(
        debug_dir=debug_dir,
        suffix=inspect.getframeinfo(inspect.currentframe()).function,
    )

    NUM_DEPTHS = 10
    NUM_EVENTS_PER_DEPTH = 100

    depths = np.linspace(0.0, 950.0, NUM_DEPTHS)
    steering_dict = {
        "run": {
            "run_id": i8(1),
            "event_id_of_first_event": i8(1),
            "observation_level_asl_m": f8(0.0),
            "earth_magnetic_field_x_muT": f8(12.5),
            "earth_magnetic_field_z_muT": f8(-25.9),
            "atmosphere_id": i8(10),
            "energy_range": {"start_GeV": f8(0.5), "stop_GeV": f8(2.0)},
        },
        "primaries": [],
    }

    seed = 1
    for depth in depths:
        for rep in range(NUM_EVENTS_PER_DEPTH):
            prm = {
                "particle_id": f8(1),
                "energy_GeV": f8(1),
                "zenith_rad": f8(0.0),
                "azimuth_rad": f8(0.0),
                "depth_g_per_cm2": f8(depth),
                "random_seed": cpw.random.seed.make_simple_seed(seed),
            }
            steering_dict["primaries"].append(prm)
            seed += 1

    num_events = len(steering_dict["primaries"])
    num_bunches = []
    num_photons = []
    std_r = []

    run_path = os.path.join(tmp.name, "different_starting_depths.tar")
    if not os.path.exists(run_path):
        cpw.corsika_primary(
            corsika_path=corsika_primary_path,
            steering_dict=steering_dict,
            output_path=run_path,
        )
    run = cpw.tario.EventTapeReader(run_path)

    for depth in depths:
        _num_bunches = []
        _num_photons = []
        _std_r = []
        for rep in range(NUM_EVENTS_PER_DEPTH):
            event = next(run)
            evth, bunches = event
            if bunches.shape[0] > 0:
                _num_bunches.append(bunches.shape[0])
                _num_photons.append(np.sum(bunches[:, cpw.I.BUNCH.BSIZE]))
                _std_r.append(
                    np.hypot(
                        np.std(bunches[:, cpw.I.BUNCH.X]),
                        np.std(bunches[:, cpw.I.BUNCH.Y]),
                    )
                )
        num_bunches.append(np.mean(_num_bunches))
        num_photons.append(np.mean(_num_photons))
        std_r.append(np.mean(_std_r))

    print("num   depth   num.ph.   std.x.y.")
    for ii in range(depths.shape[0]):
        print(
            "{: 3d} {: 3.1f} {: 6.1f} {: 6.1f}".format(
                ii, depths[ii], num_photons[ii], 1e-2 * std_r[ii]
            )
        )

    # max photons is somewhere in the middle:
    # Too high -> photons are absorbed before reaching ground.
    # Too low -> shower reaches obs. level before photons can be emitted.
    depth_with_max_ph = np.argmax(num_photons)
    assert depth_with_max_ph != 0
    assert depth_with_max_ph != NUM_DEPTHS - 1

    # The spread of the light-pool should be smaller for starting points deeper
    # in the atmosphere.
    assert np.all(np.gradient(std_r) < 0)

    tmp.cleanup_when_no_debug()
