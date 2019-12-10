def pytest_addoption(parser):
    parser.addoption(
        "--corsika_path",
        action="store",
        default="./build/corsika/original/corsika-75600/run/corsika75600Linux_QGSII_urqmd")
    parser.addoption(
        "--corsika_primary_path",
        action="store",
        default="./build/corsika/modified/corsika-75600/run/corsika75600Linux_QGSII_urqmd")
    parser.addoption(
        "--merlict_eventio_converter",
        action="store",
        default="./build/merlict/merlict-eventio-converter")