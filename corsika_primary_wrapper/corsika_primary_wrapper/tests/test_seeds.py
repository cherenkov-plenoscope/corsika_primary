import corsika_primary_wrapper as cpw
import numpy as np
import pytest


crss = cpw.random_seed.CorsikaRandomSeed(
    NUM_DIGITS_RUN_ID=6, NUM_DIGITS_AIRSHOWER_ID=3
)


def test_valid_airshower_id():
    assert not crss.is_valid_airshower_id(-1)
    assert crss.is_valid_airshower_id(0)
    assert crss.is_valid_airshower_id(1)

    assert crss.is_valid_airshower_id(crss.NUM_AIRSHOWER_IDS_IN_RUN - 1)
    assert not crss.is_valid_airshower_id(crss.NUM_AIRSHOWER_IDS_IN_RUN)


def test_valid_run_id():
    assert not crss.is_valid_run_id(-1)
    assert crss.is_valid_run_id(0)
    assert crss.is_valid_run_id(1)

    assert crss.is_valid_run_id(crss.NUM_RUN_IDS - 1)
    assert not crss.is_valid_run_id(crss.NUM_RUN_IDS)


def test_seed_limit_run_id():
    seed = crss.random_seed_based_on(
        run_id=crss.NUM_RUN_IDS - 1, airshower_id=1
    )
    assert crss.NUM_RUN_IDS - 1 == crss.run_id_from_seed(seed=seed)
    assert 1 == crss.airshower_id_from_seed(seed=seed)

    with pytest.raises(AssertionError) as e:
        crss.random_seed_based_on(run_id=crss.NUM_RUN_IDS, airshower_id=1)


def test_seed_limit_airshower_id():
    seed = crss.random_seed_based_on(
        run_id=1, airshower_id=crss.NUM_AIRSHOWER_IDS_IN_RUN - 1,
    )
    assert crss.NUM_AIRSHOWER_IDS_IN_RUN - 1 == crss.airshower_id_from_seed(
        seed=seed
    )
    assert 1 == crss.run_id_from_seed(seed=seed)

    with pytest.raises(AssertionError) as e:
        crss.random_seed_based_on(
            run_id=0, airshower_id=crss.NUM_AIRSHOWER_IDS_IN_RUN,
        )


def test_seed_combinations():
    np.random.seed(0)
    run_ids = np.random.uniform(0, crss.NUM_RUN_IDS - 1, size=300).astype("i4")
    airshower_ids = np.random.uniform(
        0, crss.NUM_AIRSHOWER_IDS_IN_RUN - 1, size=300
    ).astype("i4")

    for run_id in run_ids:
        for airshower_id in airshower_ids:
            seed = crss.random_seed_based_on(
                run_id=run_id, airshower_id=airshower_id
            )
            np.random.seed(seed)
            assert crss.run_id_from_seed(seed=seed) == run_id
            assert crss.airshower_id_from_seed(seed=seed) == airshower_id


def test_seed_num_digits():
    assert crss.NUM_DIGITS_SEED >= 6
    assert crss.NUM_DIGITS_SEED <= 12
    assert crss.NUM_SEEDS < np.iinfo(np.int32).max


def test_template_string():
    np.random.seed(0)
    run_ids = np.random.uniform(0, crss.NUM_RUN_IDS - 1, size=30).astype("i4")
    airshower_ids = np.random.uniform(
        0, crss.NUM_AIRSHOWER_IDS_IN_RUN - 1, size=30
    ).astype("i4")

    for run_id in run_ids:
        for airshower_id in airshower_ids:
            seed = crss.random_seed_based_on(
                run_id=run_id, airshower_id=airshower_id
            )
            s = crss.SEED_TEMPLATE_STR.format(seed=seed)
            assert int(s) == seed
            assert len(s) == crss.NUM_DIGITS_SEED


def test_raise_when_seed_too_big():
    c = cpw.random_seed.CorsikaRandomSeed(
        NUM_DIGITS_RUN_ID=6, NUM_DIGITS_AIRSHOWER_ID=3
    )

    with pytest.raises(AssertionError) as e:
        c = cpw.random_seed.CorsikaRandomSeed(
            NUM_DIGITS_RUN_ID=6, NUM_DIGITS_AIRSHOWER_ID=4
        )

    with pytest.raises(AssertionError) as e:
        c = cpw.random_seed.CorsikaRandomSeed(
            NUM_DIGITS_RUN_ID=7, NUM_DIGITS_AIRSHOWER_ID=3
        )
