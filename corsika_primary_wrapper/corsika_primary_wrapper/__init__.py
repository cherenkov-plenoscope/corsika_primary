import numpy as np
import tempfile
import os
import subprocess
import shutil
import io
import tarfile
import struct
import copy
from . import random_distributions
from . import random_seed
from . import collect_version_information
from . import steering


CM2M = 1e-2
M2CM = 1.0 / CM2M
MAX_ZENITH_DEG = 70.0


NUM_BYTES_PER_BUNCH = (
    len(["x", "y", "cx", "cy", "t", "zem", "wvl", "size"]) * 4
)
IX = 0
IY = 1
ICX = 2
ICY = 3
ITIME = 4
IZEM = 5
IBSIZE = 6
IWVL = 7


def corsika_primary(
    corsika_path,
    steering_dict,
    output_path,
    stdout_path=None,
    stderr_path=None,
    tmp_dir_prefix="corsika_primary_",
):
    """
    Call CORSIKA-primary and write Cherenkov-photons to output_path.

    This call is threadsafe, all execution takes place in a temproary copy
    of CORSIKA's run-directory.

    Parameters
    ----------
        corsika_path : str
            Path to corsika's executable in its 'run' directory.
        steering_dict : dict
            The steering for the run and for each primary particle.
        output_path : str
            Path to tape-archive with Cherenkov-photons.
        stdout_path : str
            Path to write CORSIKA's std-out to.
            If None: output_path + 'stdout'
        stderr_path : str
            Path to write CORSIKA's std-error to.
            If None: output_path + 'stderr'
    """
    op = os.path
    corsika_path = op.abspath(corsika_path)
    steering_dict = copy.deepcopy(steering_dict)
    output_path = op.abspath(output_path)
    stdout_path = stdout_path if stdout_path else output_path + ".stdout"
    stderr_path = stderr_path if stderr_path else output_path + ".stderr"
    stdout_path = op.abspath(stdout_path)
    stderr_path = op.abspath(stderr_path)

    steering.assert_values(steering_dict=steering_dict)

    steering_card = steering.make_run_card_str(
        steering_dict=steering_dict, output_path=output_path,
    )
    primary_bytes = steering.primary_dicts_to_bytes(
        primary_dicts=steering_dict["primaries"]
    )

    corsika_run_dir = op.dirname(corsika_path)

    with tempfile.TemporaryDirectory(prefix=tmp_dir_prefix) as tmp_dir:
        tmp_corsika_run_dir = op.join(tmp_dir, "run")
        shutil.copytree(corsika_run_dir, tmp_corsika_run_dir, symlinks=False)
        tmp_corsika_path = op.join(
            tmp_corsika_run_dir, op.basename(corsika_path)
        )
        primary_path = op.join(
            tmp_corsika_run_dir,
            steering.PRIMARY_BYTES_FILENAME_IN_CORSIKA_RUN_DIR,
        )
        with open(primary_path, "wb") as f:
            f.write(primary_bytes)

        steering_card_pipe, pwrite = os.pipe()
        os.write(pwrite, str.encode(steering_card))
        os.close(pwrite)

        with open(stdout_path, "w") as stdout, open(
            stderr_path, "w"
        ) as stderr:
            rc = subprocess.call(
                tmp_corsika_path,
                stdin=steering_card_pipe,
                stdout=stdout,
                stderr=stderr,
                cwd=tmp_corsika_run_dir,
            )

        if op.isfile(output_path):
            os.chmod(output_path, 0o664)

    with open(stdout_path, "rt") as f:
        stdout_txt = f.read()
    assert stdout_ends_with_end_of_run_marker(stdout_txt)

    return rc


def corsika_vanilla(
    corsika_path,
    steering_card,
    output_path,
    stdout_path=None,
    stderr_path=None,
    tmp_dir_prefix="corsika_primary_",
):
    """
    Call vanilla CORSIKA-7.56 and write Cherenkov-photons to output_path.

    This call is threadsafe, all execution takes place in a temproary copy
    of CORSIKA's run-directory.

    Parameters
    ----------
        corsika_path : str
            Path to corsika's executable in its 'run' directory.
        steering_card : str
            The steering-card for vanilla CORSIKA-7.56.
        output_path : str
            Path to eventio-file with Cherenkov-photons.
        stdout_path : str
            Path to write CORSIKA's std-out to.
            If None: output_path + 'stdout'
        stderr_path : str
            Path to write CORSIKA's std-error to.
            If None: output_path + 'stderr'
    """
    op = os.path
    corsika_path = op.abspath(corsika_path)
    steering_card = str(steering_card)
    assert steering_card[-1] == "\n", "Newline to end stdin for CORSIKA."
    output_path = op.abspath(output_path)
    stdout_path = stdout_path if stdout_path else output_path + ".stdout"
    stderr_path = stderr_path if stderr_path else output_path + ".stderr"
    stdout_path = op.abspath(stdout_path)
    stderr_path = op.abspath(stderr_path)

    corsika_run_dir = op.dirname(corsika_path)

    with tempfile.TemporaryDirectory(prefix=tmp_dir_prefix) as tmp_dir:
        tmp_corsika_run_dir = op.join(tmp_dir, "run")
        shutil.copytree(corsika_run_dir, tmp_corsika_run_dir, symlinks=False)
        tmp_corsika_path = op.join(
            tmp_corsika_run_dir, op.basename(corsika_path)
        )
        steering_card_pipe, pwrite = os.pipe()
        os.write(pwrite, str.encode(steering_card))
        os.close(pwrite)

        with open(stdout_path, "w") as stdout, open(
            stderr_path, "w"
        ) as stderr:
            rc = subprocess.call(
                tmp_corsika_path,
                stdin=steering_card_pipe,
                stdout=stdout,
                stderr=stderr,
                cwd=tmp_corsika_run_dir,
            )

        if op.isfile(output_path):
            os.chmod(output_path, 0o664)

    with open(stdout_path, "rt") as f:
        stdout_txt = f.read()
    assert stdout_ends_with_end_of_run_marker(stdout_txt)

    return rc


RUNH_MARKER_FLOAT32 = struct.unpack("f", "RUNH".encode())[0]
EVTH_MARKER_FLOAT32 = struct.unpack("f", "EVTH".encode())[0]

TARIO_RUNH_FILENAME = "runh.float32"
TARIO_EVTH_FILENAME = "{:09d}.evth.float32"
TARIO_BUNCHES_FILENAME = "{:09d}.cherenkov_bunches.Nx8_float32"


class Tario:
    def __init__(self, path):
        self.path = path
        self.tar = tarfile.open(path, "r|*")

        runh_tar = self.tar.next()
        runh_bin = self.tar.extractfile(runh_tar).read()
        self.runh = np.frombuffer(runh_bin, dtype=np.float32)
        assert self.runh[0] == RUNH_MARKER_FLOAT32
        self.num_events_read = 0

    def __next__(self):
        evth_tar = self.tar.next()
        if evth_tar is None:
            raise StopIteration
        evth_number = int(evth_tar.name[0:9])
        evth_bin = self.tar.extractfile(evth_tar).read()
        evth = np.frombuffer(evth_bin, dtype=np.float32)
        assert evth[0] == EVTH_MARKER_FLOAT32
        assert int(np.round(evth[1])) == evth_number

        bunches_tar = self.tar.next()
        bunches_number = int(bunches_tar.name[0:9])
        assert evth_number == bunches_number
        bunches_bin = self.tar.extractfile(bunches_tar).read()
        bunches = np.frombuffer(bunches_bin, dtype=np.float32)
        num_bunches = bunches.shape[0] // (8)

        self.num_events_read += 1
        return (evth, np.reshape(bunches, newshape=(num_bunches, 8)))

    def __iter__(self):
        return self

    def __exit__(self):
        self.tar.close()

    def __repr__(self):
        out = "{:s}(path='{:s}', read={:d})".format(
            self.__class__.__name__, self.path, self.num_events_read
        )
        return out


NUM_RANDOM_SEQUENCES = 4


def stdout_ends_with_end_of_run_marker(stdout):
    """
    According to CORSIKA-author Heck, this is the only sane way to check
    whether CORSIKA has finished.
    """
    lines = stdout.split("\n")
    if len(lines) < 2:
        return False

    second_last_line = lines[-2]
    MARKER = (
        " "
        + "=========="
        + " END OF RUN "
        + "================================================"
    )
    if MARKER in second_last_line:
        return True
    else:
        return False


def _parse_random_seeds_from_corsika_stdout(stdout):
    events = []
    MARKER = " AND RANDOM NUMBER GENERATOR AT BEGIN OF EVENT :"
    lines = stdout.split("\n")
    idx = 0
    while idx < len(lines):
        if MARKER in lines[idx]:
            _seeds = [None] * NUM_RANDOM_SEQUENCES
            _calls = [None] * NUM_RANDOM_SEQUENCES
            _billions = [None] * NUM_RANDOM_SEQUENCES
            event_number = int(lines[idx][49:57])
            assert len(events) + 1 == event_number

            for seq in np.arange(0, NUM_RANDOM_SEQUENCES):
                is_sequence = False
                while idx < len(lines) and not is_sequence:
                    idx += 1
                    match = " SEQUENCE =  {:d}  SEED =".format(seq + 1)
                    is_sequence = str.find(lines[idx], match) == 0
                _seeds[seq] = int(lines[idx][22:33])
                _calls[seq] = int(lines[idx][41:52])
                _billions[seq] = int(lines[idx][63:73])

            state = []
            for seq in np.arange(0, NUM_RANDOM_SEQUENCES):
                state.append(
                    {
                        "SEED": np.int32(_seeds[seq]),
                        "CALLS": np.int32(_calls[seq]),
                        "BILLIONS": np.int32(_billions[seq]),
                    }
                )
            events.append(state)
        idx += 1
    return events


def _parse_num_bunches_from_corsika_stdout(stdout):
    marker = " Total number of photons in shower:"
    nums = []
    lines = stdout.split("\n")
    for ll in range(len(lines)):
        pos = lines[ll].find(" Total number of photons in shower:")
        if pos == 0:
            work_line = lines[ll][len(marker) : -1]
            pos_2nd_in = work_line.find("in")
            work_line = work_line[pos_2nd_in + 2 : -len("bunch") - 1]
            nums.append(int(float(work_line)))
    return nums


class CorsikaPrimary:
    def __init__(
        self,
        corsika_path,
        steering_dict,
        stdout_path,
        stderr_path,
        tmp_dir_prefix="corsika_primary_",
    ):
        """
        Inits a run-handle which can return the next event on demand.
        No output is written.

        Parameters
        ----------
        corsika_path : str
            Path to corsika's executable in its 'run' directory.
        steering_dict : dict
            The steering for the run and for each primary particle.
        stdout_path : str
            Path to write CORSIKA's std-out to.
        stderr_path : str,
            Path to write CORSIKA's std-error to.
        """
        op = os.path

        self.corsika_path = op.abspath(corsika_path)
        self.steering_dict = copy.deepcopy(steering_dict)
        self.stdout_path = op.abspath(stdout_path)
        self.stderr_path = op.abspath(stderr_path)
        self.tmp_dir_prefix = str(tmp_dir_prefix)

        steering.assert_values(steering_dict=self.steering_dict)

        self.tmp_dir_handle = tempfile.TemporaryDirectory(
            prefix=self.tmp_dir_prefix
        )
        self.tmp_dir = self.tmp_dir_handle.name

        self.fifo_path = op.join(self.tmp_dir, "fifo.tar")
        os.mkfifo(self.fifo_path)

        self.tmp_corsika_run_dir = op.join(self.tmp_dir, "run")
        self.corsika_run_dir = op.dirname(self.corsika_path)

        shutil.copytree(
            self.corsika_run_dir, self.tmp_corsika_run_dir, symlinks=False
        )
        self.tmp_corsika_path = op.join(
            self.tmp_corsika_run_dir, op.basename(self.corsika_path)
        )

        self.steering_card = steering.make_run_card_str(
            steering_dict=self.steering_dict, output_path=self.fifo_path,
        )
        assert self.steering_card[-1] == "\n", "Need newline to mark ending."

        self.primary_bytes = steering.primary_dicts_to_bytes(
            primary_dicts=self.steering_dict["primaries"],
        )

        self.primary_path = op.join(
            self.tmp_corsika_run_dir,
            steering.PRIMARY_BYTES_FILENAME_IN_CORSIKA_RUN_DIR,
        )
        with open(self.primary_path, "wb") as f:
            f.write(self.primary_bytes)

        self.stdout = open(self.stdout_path, "w")
        self.stderr = open(self.stderr_path, "w")

        self.corsika_process = subprocess.Popen(
            self.tmp_corsika_path,
            stdout=self.stdout,
            stderr=self.stderr,
            stdin=subprocess.PIPE,
            cwd=self.tmp_corsika_run_dir,
        )
        self.corsika_process.stdin.write(str.encode(self.steering_card))
        self.corsika_process.stdin.flush()

        self.tario_reader = Tario(path=self.fifo_path)
        self.runh = self.tario_reader.runh

    def _close(self):
        self.tario_reader.__exit__()
        self.stdout.close()
        self.stderr.close()
        with open(self.stdout_path, "rt") as f:
            stdout_txt = f.read()
        self.exit_ok = stdout_ends_with_end_of_run_marker(stdout_txt)
        self.tmp_dir_handle.cleanup()

    def __next__(self):
        try:
            return self.tario_reader.__next__()
        except StopIteration:
            self._close()
            raise

    def __iter__(self):
        return self

    def __repr__(self):
        out = "{:s}(path='{:s}', tmp_dir='{:s}')".format(
            self.__class__.__name__, self.corsika_path, self.tmp_dir
        )
        return out


# From CORSIKA manual
# --------------

# RUNHEADER
# ---------
I_RUNH_NUM_EVENTS = 93 - 1

# EVENTHEADER
# -----------
I_EVTH_MARKER = 1 - 1
I_EVTH_EVENT_NUMBER = 2 - 1
I_EVTH_PARTICLE_ID = 3 - 1
I_EVTH_TOTAL_ENERGY_GEV = 4 - 1
I_EVTH_STARTING_DEPTH_G_PER_CM2 = 5 - 1
I_EVTH_NUMBER_OF_FIRST_TARGET_IF_FIXED = 6 - 1
I_EVTH_Z_FIRST_INTERACTION_CM = 7 - 1
I_EVTH_PX_MOMENTUM_GEV_PER_C = 8 - 1
I_EVTH_PY_MOMENTUM_GEV_PER_C = 9 - 1
I_EVTH_PZ_MOMENTUM_GEV_PER_C = 10 - 1
I_EVTH_ZENITH_RAD = 11 - 1
I_EVTH_AZIMUTH_RAD = 12 - 1

I_EVTH_NUM_DIFFERENT_RANDOM_SEQUENCES = 13 - 1


def I_EVTH_RANDOM_SEED(sequence):
    assert sequence >= 1
    assert sequence <= 10
    return (11 + 3 * sequence) - 1


def I_EVTH_RANDOM_SEED_CALLS(sequence):
    assert sequence >= 1
    assert sequence <= 10
    return (12 + 3 * sequence) - 1


def I_EVTH_RANDOM_SEED_MILLIONS(sequence):
    """
    This is actually 10**6, but the input to corsika is billions 10**9
    """
    assert sequence >= 1
    assert sequence <= 10
    return (13 + 3 * sequence) - 1


I_EVTH_RUN_NUMBER = 44 - 1
I_EVTH_DATE_OF_BEGIN_RUN = 45 - 1
I_EVTH_VERSION_OF_PROGRAM = 46 - 1

I_EVTH_NUM_OBSERVATION_LEVELS = 47 - 1


def I_EVTH_HEIGHT_OBSERVATION_LEVEL(level):
    assert level >= 1
    assert level <= 10
    return (47 + level) - 1


I_EVTH_EARTH_MAGNETIC_FIELD_X_UT = 71 - 1
I_EVTH_EARTH_MAGNETIC_FIELD_X_UT = 72 - 1

I_EVTH_ANGLE_X_MAGNETIG_NORTH_RAD = 93 - 1

I_EVTH_NUM_REUSES_OF_CHERENKOV_EVENT = 98 - 1


def I_EVTH_X_CORE_CM(reuse):
    assert reuse >= 1
    assert reuse <= 20
    return (98 + reuse) - 1


def I_EVTH_Y_CORE_CM(reuse):
    assert reuse >= 1
    assert reuse <= 20
    return (118 + reuse) - 1


I_EVTH_STARTING_HEIGHT_CM = 158 - 1


def event_seed_from_evth(evth):
    MILLION = np.int64(1000 * 1000)
    BILLION = np.int64(1000 * 1000 * 1000)

    def ftoi(val):
        val_i = np.int64(val)
        assert val_i == val
        return val_i

    nseq = ftoi(evth[I_EVTH_NUM_DIFFERENT_RANDOM_SEQUENCES])

    seeds = []
    for seq_idx in range(nseq):
        seq_id = seq_idx + 1

        seed = ftoi(evth[I_EVTH_RANDOM_SEED(sequence=seq_id)])
        calls = ftoi(evth[I_EVTH_RANDOM_SEED_CALLS(sequence=seq_id)])
        millions = ftoi(evth[I_EVTH_RANDOM_SEED_MILLIONS(sequence=seq_id)])

        total_calls = millions * MILLION + calls
        calls_mod_billions = np.mod(total_calls, BILLION)
        calls_billions = total_calls // BILLION

        seq = {
            "SEED": int(seed),
            "CALLS": int(calls_mod_billions),
            "BILLIONS": int(calls_billions),
        }
        seeds.append(seq)
    return seeds
