import pytest
import corsika_primary as cpw
import inspect
import numpy as np
import copy
import tempfile
import os

i8 = np.int64
f8 = np.float64


@pytest.fixture()
def corsika_primary_path(pytestconfig):
    return pytestconfig.getoption("corsika_primary_path")


@pytest.fixture()
def debug_dir(pytestconfig):
    return pytestconfig.getoption("debug_dir")


def test_particle_output_stream(corsika_primary_path, debug_dir):
    tmp = cpw.testing.TmpDebugDir(
        debug_dir=debug_dir,
        suffix=inspect.getframeinfo(inspect.currentframe()).function,
    )

    run_path = os.path.join(tmp.name, "1")

    steering = cpw.testing.make_example_steering_for_particle_output()

    with cpw.CorsikaPrimary(
        corsika_path=corsika_primary_path,
        steering_dict=steering,
        stdout_path=run_path + ".o",
        stderr_path=run_path + ".e",
    ) as run:

        for event in run:
            evth, cer_bunches, par_bunches = event

            print("------------------------------------")

            for cer_ii, cer_b in enumerate(cer_bunches):
                print("cer", cer_ii, len(cer_b))

            for par_ii, par_b in enumerate(par_bunches):
                print("par", par_ii, len(par_b))

    tmp.cleanup_when_no_debug()
