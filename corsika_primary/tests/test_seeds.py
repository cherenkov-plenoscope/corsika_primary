import corsika_primary as cpw
import numpy as np
import pytest

NN = 1000
crss = cpw.random.seed.RunIdEventIdSeedStructure(num_events_in_run=NN)


def test_valid_airshower_id():
    assert not crss.is_valid_event_id(-1)
    assert not crss.is_valid_event_id(0)
    assert crss.is_valid_event_id(1)

    assert crss.is_valid_event_id(NN)
    assert not crss.is_valid_event_id(NN + 1)


def test_valid_run_id():
    assert not crss.is_valid_run_id(-1)
    assert not crss.is_valid_run_id(0)
    assert crss.is_valid_run_id(1)

    assert crss.is_valid_run_id(crss.max_run_id)
    assert not crss.is_valid_run_id(crss.max_run_id + 1)


def test_seed_upper_limit():
    seed = crss.seed_based_on(run_id=899999, event_id=1000)
    assert seed == 900000000
    assert 899999 == crss.run_id_from_seed(seed=seed)
    assert 1000 == crss.event_id_from_seed(seed=seed)

    with pytest.raises(AssertionError) as e:
        crss.seed_based_on(run_id=900000, event_id=1)

    with pytest.raises(AssertionError) as e:
        crss.seed_based_on(run_id=899999, event_id=1001)


def test_seed_lower_limit():
    seed = crss.seed_based_on(run_id=1, event_id=1)
    assert seed == 1000 + 1
    assert 1 == crss.run_id_from_seed(seed=seed)
    assert 1 == crss.event_id_from_seed(seed=seed)

    with pytest.raises(AssertionError) as e:
        crss.seed_based_on(run_id=1, event_id=0)

    with pytest.raises(AssertionError) as e:
        crss.seed_based_on(run_id=0, event_id=1)


def test_seed_combinations():
    prng = np.random.Generator(np.random.MT19937(seed=0))

    for num in [3, 42, 100, 1337, 25000]:
        c = cpw.random.seed.RunIdEventIdSeedStructure(num_events_in_run=num)
        run_ids = prng.uniform(1, c.max_run_id, size=100).astype("i4")
        event_ids = prng.uniform(1, c.num_events_in_run, size=100).astype("i4")

        for run_id in run_ids:
            for event_id in event_ids:
                seed = c.seed_based_on(run_id=run_id, event_id=event_id)
                assert c.run_id_from_seed(seed=seed) == run_id
                assert c.event_id_from_seed(seed=seed) == event_id


def test_seed_num_digits():
    assert crss.NUM_DIGITS_SEED == 9


def test_template_string():
    prng = np.random.Generator(np.random.MT19937(seed=0))

    for num in [3, 42, 100, 1337, 25000]:
        c = cpw.random.seed.RunIdEventIdSeedStructure(num_events_in_run=num)
        run_ids = prng.uniform(1, c.max_run_id, size=25).astype("i4")
        event_ids = prng.uniform(1, c.num_events_in_run, size=25).astype("i4")

        for run_id in run_ids:
            for event_id in event_ids:
                seed = c.seed_based_on(run_id=run_id, event_id=event_id)
                s = c.SEED_TEMPLATE_STR.format(seed=seed)
                assert int(s) == seed
                assert len(s) == c.NUM_DIGITS_SEED


def test_raise_when_seed_too_big():
    c = cpw.random.seed.RunIdEventIdSeedStructure(num_events_in_run=1)

    with pytest.raises(AssertionError) as e:
        cpw.random.seed.RunIdEventIdSeedStructure(num_events_in_run=0)

    with pytest.raises(AssertionError) as e:
        cpw.random.seed.RunIdEventIdSeedStructure(num_events_in_run=1000000000)


def test_no_duplicate_seeds():
    NUM_R = 10
    NUM_E = 100
    c = cpw.random.seed.RunIdEventIdSeedStructure(num_events_in_run=100)
    seeds = set()
    for run_id in np.arange(1, NUM_R + 1):
        for event_id in np.arange(1, NUM_E + 1):
            seed = c.seed_based_on(run_id=run_id, event_id=event_id)
            assert seed not in seeds
            seeds.add(seed)
    assert len(seeds) == NUM_R * NUM_E

    # assert continues increment by 1
    # -------------------------------
    seed_array = np.array(list(seeds))
    seed_array.sort()
    assert np.all(np.gradient(seed_array) == 1)
