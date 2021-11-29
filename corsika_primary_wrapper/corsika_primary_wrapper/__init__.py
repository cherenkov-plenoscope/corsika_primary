import numpy as np
import tempfile
import os
import subprocess
import shutil
import io
import tarfile
import struct
from . import random_distributions
from . import random_seed
from . import collect_version_information
from . import steering_io
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
    stdout_postfix=".stdout",
    stderr_postfix=".stderr",
    tmp_dir_prefix="corsika_primary_",
):
    """
    Call CORSIKA-primary mod

    Parameters
    ----------
        corsika_path    Path to corsika's executable in its 'run' directory.

        steering_dict   Dictionary describing the environment, and all primary
                        particles explicitly.

        output_path     Path to output tape-archive with Cherenkov-photons.
    """
    steering_card, primary_bytes = _dict_to_card_and_bytes(steering_dict)
    return explicit_corsika_primary(
        corsika_path=corsika_path,
        steering_card=steering_card,
        primary_bytes=primary_bytes,
        output_path=output_path,
        stdout_postfix=stdout_postfix,
        stderr_postfix=stderr_postfix,
        tmp_dir_prefix=tmp_dir_prefix,
    )


def explicit_corsika_primary(
    corsika_path,
    steering_card,
    primary_bytes,
    output_path,
    stdout_postfix=".stdout",
    stderr_postfix=".stderr",
    tmp_dir_prefix="corsika_primary_",
):
    """
    Call CORSIKA-primary mod

    Parameters
    ----------
        corsika_path    Path to corsika's executable in its 'run' directory.

        steering_card   String of lines seperated by newline.
                        Steers all constant properties of a run.

        primary_bytes   Bytes [5 x float64, 12 x int32] for each
                        primary particle. The number of primaries will
                        overwrite NSHOW in steering_card.

        output_path     Path to output tape-archive with Cherenkov-photons.
    """
    op = os.path
    corsika_path = op.abspath(corsika_path)
    output_path = op.abspath(output_path)

    out_dirname = op.dirname(output_path)
    out_basename = op.basename(output_path)
    o_path = op.join(out_dirname, out_basename + stdout_postfix)
    e_path = op.join(out_dirname, out_basename + stderr_postfix)
    corsika_run_dir = op.dirname(corsika_path)
    num_primaries = len(primary_bytes) // NUM_BYTES_PER_PRIMARY
    assert (len(primary_bytes) % NUM_BYTES_PER_PRIMARY) == 0

    with tempfile.TemporaryDirectory(prefix=tmp_dir_prefix) as tmp_dir:
        tmp_corsika_run_dir = op.join(tmp_dir, "run")
        shutil.copytree(corsika_run_dir, tmp_corsika_run_dir, symlinks=False)
        tmp_corsika_path = op.join(
            tmp_corsika_run_dir, op.basename(corsika_path)
        )

        primary_path = op.join(
            tmp_corsika_run_dir, PRIMARY_BYTES_FILENAME_IN_CORSIKA_RUN_DIR
        )
        with open(primary_path, "wb") as f:
            f.write(primary_bytes)

        steering_card = _overwrite_steering_card(
            steering_card=steering_card,
            output_path=output_path,
            num_shower=num_primaries,
        )

        steering_card_pipe, pwrite = os.pipe()
        os.write(pwrite, str.encode(steering_card))
        os.close(pwrite)

        with open(o_path, "w") as stdout, open(e_path, "w") as stderr:
            rc = subprocess.call(
                tmp_corsika_path,
                stdin=steering_card_pipe,
                stdout=stdout,
                stderr=stderr,
                cwd=tmp_corsika_run_dir,
            )

        if op.isfile(output_path):
            os.chmod(output_path, 0o664)

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
                        "SEED": _seeds[seq],
                        "CALLS": _calls[seq],
                        "BILLIONS": _billions[seq],
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
        stdout_path,
        stderr_path,
        steering_card,
        primary_bytes,
        tmp_dir_prefix="corsika_primary_",
    ):
        self.corsika_path = str(corsika_path)
        self.stdout_path = str(stdout_path)
        self.stderr_path = str(stderr_path)
        self.steering_card = str(steering_card)
        self.primary_bytes = bytes(primary_bytes)

        self.num_primaries = len(self.primary_bytes) // NUM_BYTES_PER_PRIMARY
        assert (len(self.primary_bytes) % NUM_BYTES_PER_PRIMARY) == 0
        assert self.num_primaries > 0

        self.tmp_dir_handle = tempfile.TemporaryDirectory(
            prefix=tmp_dir_prefix
        )
        self.tmp_dir = self.tmp_dir_handle.name

        self.fifo_path = os.path.join(self.tmp_dir, "fifo.tar")
        os.mkfifo(self.fifo_path)

        self.tmp_corsika_run_dir = os.path.join(self.tmp_dir, "run")
        self.corsika_run_dir = os.path.dirname(self.corsika_path)

        shutil.copytree(
            self.corsika_run_dir, self.tmp_corsika_run_dir, symlinks=False
        )
        self.tmp_corsika_path = os.path.join(
            self.tmp_corsika_run_dir, os.path.basename(self.corsika_path)
        )

        self.primary_path = os.path.join(
            self.tmp_corsika_run_dir, PRIMARY_BYTES_FILENAME_IN_CORSIKA_RUN_DIR
        )
        with open(self.primary_path, "wb") as f:
            f.write(self.primary_bytes)

        self.steering_card = _overwrite_steering_card(
            steering_card=self.steering_card,
            output_path=self.fifo_path,
            num_shower=self.num_primaries,
        )
        self.steering_card += "\n"

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
    return (21 + 3 * sequence) - 1


def I_EVTH_RANDOM_SEED_BILLIONS(sequence):
    assert sequence >= 1
    assert sequence <= 10
    return (31 + 3 * sequence) - 1


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
