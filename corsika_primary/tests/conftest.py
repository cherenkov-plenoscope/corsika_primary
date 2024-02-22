import os

CORSIKA_PATH = os.path.join(
    ".",
    "build",
    "corsika",
    "{flavor:s}",
    "corsika-75600",
    "run",
    "corsika75600Linux_QGSII_urqmd",
)


def pytest_addoption(parser):
    parser.addoption(
        "--corsika_vanilla_path",
        action="store",
        default=CORSIKA_PATH.format(flavor="vanilla"),
    )
    parser.addoption(
        "--corsika_primary_path",
        action="store",
        default=CORSIKA_PATH.format(flavor="modified"),
    )
    parser.addoption(
        "--merlict_eventio_converter",
        action="store",
        default=os.path.join(
            ".",
            "build",
            "merlict_development_kit",
            "merlict-eventio-converter",
        ),
    )
    parser.addoption("--debug_dir", action="store", default="")
