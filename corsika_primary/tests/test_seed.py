import pytest
import numpy as np
import corsika_primary as cpw


def test_csv_dumps_loads():
    NUM_EVENTS = 100
    prng = np.random.Generator(np.random.PCG64(42))
    seeds = {}
    for event_id in np.arange(1, NUM_EVENTS + 1):
        seeds[event_id] = []
        for seq in range(cpw.random.seed.NUM_RANDOM_SEQUENCES):
            kk = {}
            for key in ["SEED", "CALLS", "BILLIONS"]:
                kk[key] = np.int32(prng.uniform(low=0.0, high=1e6, size=1)[0])
            seeds[event_id].append(kk)

    csv = cpw.random.seed.dumps(seeds=seeds)

    seeds_back = cpw.random.seed.loads(s=csv)

    for event_id in seeds:
        orig = seeds[event_id]
        back = seeds_back[event_id]

        for seq in range(cpw.random.seed.NUM_RANDOM_SEQUENCES):
            for key in ["SEED", "CALLS", "BILLIONS"]:
                assert orig[seq][key] == back[seq][key]
