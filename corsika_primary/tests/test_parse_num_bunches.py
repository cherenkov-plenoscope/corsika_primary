import corsika_primary as cpw
import os
from importlib import resources as importlib_resources


resource_dir = os.path.join(
    importlib_resources.files("corsika_primary"), "tests", "resources"
)


def test_parse_num_bunches():
    path = os.path.join(resource_dir, "example_vanilla_corsika.stdout")
    with open(path, "rt") as f:
        stdout = f.read()
    actual_num_bunches = cpw.testing.parse_num_bunches_from_corsika_stdout(
        stdout=stdout
    )
    expected_num_bunches = [50053, 57921, 38977, 42614, 29591, 37821, 33591]

    assert len(actual_num_bunches) == len(expected_num_bunches)
    for evt in range(len(actual_num_bunches)):
        assert actual_num_bunches[evt] == expected_num_bunches[evt]
