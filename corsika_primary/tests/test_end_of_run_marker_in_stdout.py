import corsika_primary as cpw
import os
from importlib import resources as importlib_resources


resource_dir = os.path.join(
    importlib_resources.files("corsika_primary"), "tests", "resources"
)


def test_parsing_random_state_gamma():
    path = os.path.join(resource_dir, "example_vanilla_corsika.stdout")
    with open(path, "rt") as f:
        stdout = f.read()
    assert cpw.testing.stdout_ends_with_end_of_run_marker(stdout=stdout)


def test_empty_stdout():
    o = ""
    assert cpw.testing.stdout_ends_with_end_of_run_marker(stdout=o) == False

    o = "one"
    assert cpw.testing.stdout_ends_with_end_of_run_marker(stdout=o) == False

    o = "one\ntwo"
    assert cpw.testing.stdout_ends_with_end_of_run_marker(stdout=o) == False

    o = "one\ntwo\nthree"
    assert cpw.testing.stdout_ends_with_end_of_run_marker(stdout=o) == False
