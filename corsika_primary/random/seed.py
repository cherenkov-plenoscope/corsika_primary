import numpy as np
import io
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


def parse_seed_from_evth(evth, dtype_constructor=np.int32):
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


def csv_header():
    f = io.StringIO()
    f.write("#")
    f.write("{:>8s},".format("event_id"))
    for seq in range(NUM_RANDOM_SEQUENCES):
        for key in ["SEED", "CALLS", "BILLIONS"]:
            skey = "{:s}{:d}".format(key, seq + 1)
            f.write("{:>9s}".format(skey))
            if seq < NUM_RANDOM_SEQUENCES:
                f.write(",")
    f.write("\n")
    f.seek(0)
    return f.read()


def dumps(seeds):
    """
    Returns csv-string.

    parameters
    ----------
    seeds : dict of seeds
        The random-number-generator-state parsed from EVTH. Keys are event_ids.
    """
    f = io.StringIO()
    f.write(csv_header())
    for event_id in seeds:
        seed = seeds[event_id]
        f.write("{:9d},".format(event_id))
        for seq in range(NUM_RANDOM_SEQUENCES):
            for key in ["SEED", "CALLS", "BILLIONS"]:
                f.write("{:9d}".format(seed[seq][key]))
                if seq < NUM_RANDOM_SEQUENCES:
                    f.write(",")
        f.write("\n")
    f.seek(0)
    return f.read()


def loads(s):
    """
    Returns dict of seeds.

    parameters
    ----------
    s : str
        Csv-string storing the random-number-generator-state for each line in
        each line.
    """
    seeds = {}
    for line in str.splitlines(s):
        if "#" in line:
            continue
        split = str.split(line, ",")
        event_id = np.int32(split[0])
        seeds[event_id] = []
        i = 1
        for seq in range(NUM_RANDOM_SEQUENCES):
            kk = {}
            for key in ["SEED", "CALLS", "BILLIONS"]:
                kk[key] = np.int32(split[i])
                i += 1
            seeds[event_id].append(kk)
    return seeds
