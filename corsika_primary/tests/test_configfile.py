import pytest
import corsika_primary as cpw
import os


@pytest.fixture()
def debug_dir(pytestconfig):
    return pytestconfig.getoption("debug_dir")


@pytest.fixture()
def corsika_primary_path(pytestconfig):
    return pytestconfig.getoption("corsika_primary_path")


@pytest.fixture()
def corsika_vanilla_path(pytestconfig):
    return pytestconfig.getoption("corsika_vanilla_path")


def test_configfile(corsika_primary_path, corsika_vanilla_path):
    config = cpw.configfile.read()
    assert config["corsika_primary"] == os.path.abspath(corsika_primary_path)
    assert config["corsika_vanilla"] == os.path.abspath(corsika_vanilla_path)
