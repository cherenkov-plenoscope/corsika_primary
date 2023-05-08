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

    piped_path = os.path.join(tmp.name, "piped")

    steering = cpw.testing.make_example_steering_for_particle_output()

    pip = {"RUNH": None, "events": []}
    with cpw.CorsikaPrimary(
        corsika_path=corsika_primary_path,
        steering_dict=steering,
        stdout_path=piped_path + ".o",
        stderr_path=piped_path + ".e",
    ) as run:
        pip["RUNH"] = run.runh

        for event in run:
            evth, cer_bunches, par_bunches = event

            eve = {"EVTH": evth, "particles": [], "EVTE": None}
            print("------------------------------------")

            for cer_ii, cer_b in enumerate(cer_bunches):
                print("cer", cer_ii, len(cer_b))

            for par_ii, par_b in enumerate(par_bunches):
                print("par", par_ii, len(par_b))
                eve["particles"].append(par_b)

            eve["particles"] = np.vstack(eve["particles"])
            eve["EVTE"] = par_bunches.evte

            pip["events"].append(eve)

    fixed_path = os.path.join(tmp.name, "fixed")

    cpw.corsika_primary(
        corsika_path=corsika_primary_path,
        steering_dict=steering,
        stdout_path=fixed_path + ".o",
        stderr_path=fixed_path + ".e",
        output_path=fixed_path + ".cer.tar",
    )

    fix = cpw.particles.read_rundict(
        path=fixed_path + ".cer.tar.par.dat", num_offset_bytes=0
    )

    cpw.particles.assert_rundict_equal(fix, pip, ignore_rune=True)

    tmp.cleanup_when_no_debug()
