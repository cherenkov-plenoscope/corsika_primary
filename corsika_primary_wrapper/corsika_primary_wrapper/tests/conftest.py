import os

CORSIKA_PATH = os.path.join(
    ".",
    "build",
    "corsika",
    "{:s}",
    "corsika-75600",
    "run",
    "corsika75600Linux_QGSII_urqmd",
)


def pytest_addoption(parser):
    parser.addoption(
        "--corsika_path",
        action="store",
        default=CORSIKA_PATH.format("original"),
    )
    parser.addoption(
        "--corsika_primary_path",
        action="store",
        default=CORSIKA_PATH.format("modified"),
    )
    parser.addoption(
        "--merlict_eventio_converter",
        action="store",
        default=os.path.join(
            ".", "build", "merlict", "merlict-eventio-converter"
        ),
    )
    parser.addoption("--debug_dir", action="store", default="")
