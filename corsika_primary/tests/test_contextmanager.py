import pytest
import corsika_primary as cpw
import numpy as np
import inspect
import os


@pytest.fixture()
def debug_dir(pytestconfig):
    return pytestconfig.getoption("debug_dir")


@pytest.fixture()
def corsika_primary_path(pytestconfig):
    return pytestconfig.getoption("corsika_primary_path")


def test_with_contextmanager(debug_dir, corsika_primary_path):
    tmp = cpw.testing.TmpDebugDir(
        debug_dir=debug_dir,
        suffix=inspect.getframeinfo(inspect.currentframe()).function,
    )

    with cpw.CorsikaPrimary(
        corsika_path=corsika_primary_path,
        steering_dict=cpw.steering.EXAMPLE,
        stdout_path=os.path.join(tmp.name, "corsika.o"),
        stderr_path=os.path.join(tmp.name, "corsika.e"),
        tmp_dir_prefix="test_with_context",
    ) as run:
        assert run.runh.shape[0] == 273

        for event in run:
            evth, cer_reader, par_reader = event
            assert evth.shape[0] == 273

            for cer_block in cer_reader:
                assert cer_block.shape[1] == 8

            for par_block in par_reader:
                assert cer_block.shape[1] == 8

    tmp.cleanup_when_no_debug()


def test_without_contextmanager(debug_dir, corsika_primary_path):
    tmp = cpw.testing.TmpDebugDir(
        debug_dir=debug_dir,
        suffix=inspect.getframeinfo(inspect.currentframe()).function,
    )

    run = cpw.CorsikaPrimary(
        corsika_path=corsika_primary_path,
        steering_dict=cpw.steering.EXAMPLE,
        stdout_path=os.path.join(tmp.name, "corsika.o"),
        stderr_path=os.path.join(tmp.name, "corsika.e"),
        tmp_dir_prefix="test_without_context",
    )

    assert run.runh.shape[0] == 273

    for event in run:
        evth, cer_reader, par_reader = event
        assert evth.shape[0] == 273

        for bunch_block in cer_reader:
            assert bunch_block.shape[1] == 8

        for par_block in par_reader:
            pass

    run.close()

    tmp.cleanup_when_no_debug()
