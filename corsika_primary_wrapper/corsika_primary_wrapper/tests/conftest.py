def pytest_addoption(parser):
    parser.addoption(
        "--corsika_path",
        action="store",
        default="./original/corsika-75600/run/corsika75600Linux_QGSII_urqmd")
    parser.addoption(
        "--corsika_primary_path",
        action="store",
        default="./modified/corsika-75600/run/corsika75600Linux_QGSII_urqmd")