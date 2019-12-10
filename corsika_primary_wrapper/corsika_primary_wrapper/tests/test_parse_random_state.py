import corsika_primary_wrapper as cpw
import os
import pkg_resources


example_stdout_path = pkg_resources.resource_filename(
    'corsika_primary_wrapper',
    os.path.join(
        'tests',
        'resources',
        'example_original_corsika.stdout'
    )
)


def test_parsing_random_state():
    with open(example_stdout_path, "rt") as f:
        stdout = f.read()
    events = cpw._parse_random_seeds_from_corsika_stdout(stdout=stdout)

    expected_events = [
        [{'SEED': 1, 'CALLS': 0, 'BILLIONS': 0},
         {'SEED': 2, 'CALLS': 0, 'BILLIONS': 0},
         {'SEED': 3, 'CALLS': 0, 'BILLIONS': 0},
         {'SEED': 4, 'CALLS': 0, 'BILLIONS': 0}],
        [{'SEED': 1, 'CALLS': 0, 'BILLIONS': 0},
         {'SEED': 2, 'CALLS': 55244, 'BILLIONS': 0},
         {'SEED': 3, 'CALLS': 284658, 'BILLIONS': 0},
         {'SEED': 4, 'CALLS': 2, 'BILLIONS': 0}],
        [{'SEED': 1, 'CALLS': 0, 'BILLIONS': 0},
         {'SEED': 2, 'CALLS': 116507, 'BILLIONS': 0},
         {'SEED': 3, 'CALLS': 624237, 'BILLIONS': 0},
         {'SEED': 4, 'CALLS': 4, 'BILLIONS': 0}],
        [{'SEED': 1, 'CALLS': 0, 'BILLIONS': 0},
         {'SEED': 2, 'CALLS': 181150, 'BILLIONS': 0},
         {'SEED': 3, 'CALLS': 842363, 'BILLIONS': 0},
         {'SEED': 4, 'CALLS': 6, 'BILLIONS': 0}],
        [{'SEED': 1, 'CALLS': 0, 'BILLIONS': 0},
         {'SEED': 2, 'CALLS': 329122, 'BILLIONS': 0},
         {'SEED': 3, 'CALLS': 1110213, 'BILLIONS': 0},
         {'SEED': 4, 'CALLS': 8, 'BILLIONS': 0}],
        [{'SEED': 1, 'CALLS': 0, 'BILLIONS': 0},
         {'SEED': 2, 'CALLS': 420552, 'BILLIONS': 0},
         {'SEED': 3, 'CALLS': 1288977, 'BILLIONS': 0},
         {'SEED': 4, 'CALLS': 10, 'BILLIONS': 0}],
        [{'SEED': 1, 'CALLS': 0, 'BILLIONS': 0},
         {'SEED': 2, 'CALLS': 500802, 'BILLIONS': 0},
         {'SEED': 3, 'CALLS': 1503394, 'BILLIONS': 0},
         {'SEED': 4, 'CALLS': 12, 'BILLIONS': 0}]
    ]

    assert len(events) == len(expected_events)
    for evt in range(len(events)):
        for seq in range(cpw.NUM_RANDOM_SEQUENCES):
            for key in ["SEED", "CALLS", "BILLIONS"]:
                assert events[evt][seq][key] == expected_events[evt][seq][key]
