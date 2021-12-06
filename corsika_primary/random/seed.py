import numpy as np
from .. import I

"""
CORSIKA 7.56 userguide.pdf, section 4.3, Random Number Generator Initialization
Limit (to get independent sequences of random numbers) is:
1 ≤ ISEED(1, k) ≤ 900 000 000
"""
MIN_SEED = 1
MAX_SEED = 900 * 1000 * 1000

NUM_RANDOM_SEQUENCES = 4


def make_simple_seed(seed):
    """
    Returns the explicit random-seed for a single event.
    It steers 4 sequences.
    This simple seed follows the default seeding used in CORSIKA where each
    sequence has SEED_OF_LAST_SEQUENCE + 1.

    According to the CORSIKA-7.56 userguide, section 4.3, the

    Parameters
    ----------
    seed : int
        The seed for the sequence in the pseudo-random-number-generator.
        1 <= seed <= 900,000,000
    """
    assert seed % 1 == 0, "The seed must be an integer."
    assert MIN_SEED <= seed
    assert seed + 3 <= MAX_SEED
    i4 = np.int32
    return [
        {"SEED": i4(seed), "CALLS": i4(0), "BILLIONS": i4(0)},
        {"SEED": i4(seed + 1), "CALLS": i4(0), "BILLIONS": i4(0)},
        {"SEED": i4(seed + 2), "CALLS": i4(0), "BILLIONS": i4(0)},
        {"SEED": i4(seed + 3), "CALLS": i4(0), "BILLIONS": i4(0)},
    ]


def parse_seed_from_evth(evth, dtype_constructor=i4):
    """
    Returns random-generator-state at the begin of an event parsed from the
    event's event-header (EVTH).
    The returned state can directly be used to reproduce events.
    Four random-sequences with (SEED, CALLS, and BILLIONS).

    parameters
    ----------
    evth : np.array(dtype=np.float32), shape = (273,)
        The raw event-header.

    dtype_constructor : constructor for integers
        The integer-constructor used for the random state.
    """
    MILLION = np.int64(1000 * 1000)
    BILLION = np.int64(1000 * 1000 * 1000)

    def ftoi(val):
        val_i = np.int64(val)
        assert val_i == val
        return val_i

    nseq = ftoi(evth[I.EVTH.NUM_DIFFERENT_RANDOM_SEQUENCES])

    seeds = []
    for seq_idx in range(nseq):
        seq_id = seq_idx + 1

        seed = ftoi(evth[I.EVTH.RANDOM_SEED(sequence=seq_id)])
        calls = ftoi(evth[I.EVTH.RANDOM_SEED_CALLS(sequence=seq_id)])
        millions = ftoi(evth[I.EVTH.RANDOM_SEED_MILLIONS(sequence=seq_id)])

        total_calls = millions * MILLION + calls
        calls_mod_billions = np.mod(total_calls, BILLION)
        calls_billions = total_calls // BILLION

        seq = {
            "SEED": dtype_constructor(seed),
            "CALLS": dtype_constructor(calls_mod_billions),
            "BILLIONS": dtype_constructor(calls_billions),
        }
        seeds.append(seq)
    return seeds


def is_pos_int(val):
    if val % 1 != 0:
        return False
    if val < 1:
        return False
    return True


class RunIdEventIdSeedStructure:
    """
    This couples the (run_id, event_id) to a seed.
    This way you can test and ensure to have seeds within limits, and not to
    use a seed multiple times.
    Every (run_id, event_id) has a unique seed.
    """

    def __init__(self, num_events_in_run=1000):
        """
        parameters
        ----------
        num_events_in_run : int
            The max. number of events to be produced in a run.
        """
        assert is_pos_int(num_events_in_run)
        assert num_events_in_run < MAX_SEED
        self.num_events_in_run = num_events_in_run
        self.NUM_DIGITS_SEED = 9
        self.SEED_TEMPLATE_STR = "{seed:0" + str(self.NUM_DIGITS_SEED) + "d}"
        self.min_event_id = 1
        self.max_event_id = self.num_events_in_run
        self.min_run_id = 1
        self.max_run_id = (
            MAX_SEED - self.num_events_in_run
        ) // self.num_events_in_run

    def seed_based_on(self, run_id, event_id):
        assert self.is_valid_run_id(run_id=run_id)
        assert self.is_valid_event_id(event_id=event_id)
        seed = run_id * self.num_events_in_run + event_id
        assert self.is_valid_seed(seed=seed), "Out of CORSIKA's range."
        return seed

    def seed_str_based_on(self, run_id, event_id):
        return self.SEED_TEMPLATE_STR.format(
            seed=self.seed_based_on(run_id=run_id, event_id=event_id)
        )

    def run_id_from_seed(self, seed):
        assert is_pos_int(seed)
        return (seed - 1) // self.num_events_in_run

    def event_id_from_seed(self, seed):
        assert is_pos_int(seed)
        return seed - self.run_id_from_seed(seed) * self.num_events_in_run

    def is_valid_run_id(self, run_id):
        if not is_pos_int(run_id):
            return False
        if run_id > self.max_run_id:
            return False
        return True

    def is_valid_event_id(self, event_id):
        if not is_pos_int(event_id):
            return False
        if event_id > self.num_events_in_run:
            return False
        return True

    def is_valid_seed(self, seed):
        if not is_pos_int(seed):
            return False
        if seed < MIN_SEED:
            return False
        if seed > MAX_SEED:
            return False
        return True

    def _max_seed_for_run_id(self, run_id):
        return (run_id + 1) * self.num_events_in_run

    def __repr__(self):
        out = self.__class__.__name__
        out += "(num_events_in_run={:d})".format(self.num_events_in_run)
        return out
