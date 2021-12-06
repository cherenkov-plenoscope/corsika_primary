import corsika_primary as cpw
import os
import pkg_resources


resource_dir = pkg_resources.resource_filename(
    "corsika_primary", os.path.join("tests", "resources")
)


def test_parsing_random_state_gamma():
    path = os.path.join(resource_dir, "example_vanilla_corsika.stdout")
    with open(path, "rt") as f:
        stdout = f.read()
    assert cpw.stdout_ends_with_end_of_run_marker(stdout=stdout)


def test_empty_stdout():
    stdout = ""
    assert cpw.stdout_ends_with_end_of_run_marker(stdout=stdout) == False

    stdout = "one"
    assert cpw.stdout_ends_with_end_of_run_marker(stdout=stdout) == False

    stdout = "one\ntwo"
    assert cpw.stdout_ends_with_end_of_run_marker(stdout=stdout) == False

    stdout = "one\ntwo\nthree"
    assert cpw.stdout_ends_with_end_of_run_marker(stdout=stdout) == False
