import numpy as np
import tempfile
import os
import subprocess
import shutil
import io
import struct
import copy
from . import random
from . import collect_version_information
from . import steering
from . import I
from . import tario
from . import testing
from . import install


MAX_ZENITH_DEG = 70.0


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
    assert testing.stdout_ends_with_end_of_run_marker(stdout_txt)

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
    output_path = op.abspath(output_path)
    steering_card = steering.overwrite_telfil_in_card_str(
        card_str=steering_card, telfil=output_path
    )
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
    assert testing.stdout_ends_with_end_of_run_marker(stdout_txt)

    return rc


NUM_RANDOM_SEQUENCES = 4


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

        self.tario_reader = tario.Tario(path=self.fifo_path)
        self.runh = self.tario_reader.runh

    def _close(self):
        self.tario_reader.__exit__()
        self.stdout.close()
        self.stderr.close()
        with open(self.stdout_path, "rt") as f:
            stdout_txt = f.read()
        self.exit_ok = testing.stdout_ends_with_end_of_run_marker(stdout_txt)
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


def bunches_to_si_units(bunches):
    b = copy.deepcopy(bunches)
    b[:, I.BUNCH.X] *= 1e-2  # cm -> m
    b[:, I.BUNCH.Y] *= 1e-2  # cm -> m
    # b[:, I.BUNCH.CX]
    # b[:, I.BUNCH.CY]
    b[:, I.BUNCH.TIME] *= 1e-9  # ns -> s
    b[:, I.BUNCH.ZEM] *= 1e-2  # cm -> m
    # b[:, I.BUNCH.BSIZE] = bunches[:, I.BUNCH.BSIZE]
    b[:, I.BUNCH.WVL] = np.abs(b[:, I.BUNCH.WVL]) * 1e-9  # nm -> m
    return b
