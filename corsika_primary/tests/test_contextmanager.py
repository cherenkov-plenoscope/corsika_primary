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
        read_block_by_block=True,
        tmp_dir_prefix="test_with_context",
    ) as run:
        assert run.runh.shape[0] == 273

        for event in run:
            evth, bunch_block_reader = event
            assert evth.shape[0] == 273

            for bunch_block in bunch_block_reader:
                assert bunch_block.shape[1] == 8

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
        read_block_by_block=True,
        tmp_dir_prefix="test_without_context",
    )

    assert run.runh.shape[0] == 273

    for event in run:
        evth, bunch_block_reader = event
        assert evth.shape[0] == 273

        for bunch_block in bunch_block_reader:
            assert bunch_block.shape[1] == 8

    run.close()

    tmp.cleanup_when_no_debug()
