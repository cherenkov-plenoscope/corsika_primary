import numpy as np
import tempfile
import os
import subprocess
import shutil
import copy
from . import install
from . import steering
from . import random
from . import I
from . import event_tape
from . import testing
from . import collect_version_information
from . import calibration_light_source
from . import particles
from . import cherenkov
from . import cherenkov_bunches
from . import configfile


MAX_ZENITH_DEG = 70.0
MAX_ZENITH_RAD = np.deg2rad(MAX_ZENITH_DEG)
CM2M = 1e-2
M2CM = 1e2


def corsika_primary(
    steering_dict,
    cherenkov_output_path,
    particle_output_path,
    stdout_path=None,
    stderr_path=None,
    tmp_dir_prefix="corsika_primary_",
    corsika_path=None,
):
    """
    Call CORSIKA-primary and write Cherenkov-photons to cherenkov_output_path.

    This call is threadsafe, all execution takes place in a temproary copy
    of CORSIKA's run-directory.

    Parameters
    ----------
    steering_dict : dict
        The steering for the run and for each primary particle.
    cherenkov_output_path : str
        Path to tape-archive with Cherenkov-photons.
    particle_output_path : str
        Path to write the particle output to.
    stdout_path : str
        Path to write CORSIKA's std-out to.
        If None: cherenkov_output_path + 'stdout'
    stderr_path : str
        Path to write CORSIKA's std-error to.
        If None: cherenkov_output_path + 'stderr'
    corsika_path : str (default: None)
        Path to corsika's executable in its 'run' directory.
        This is the modified corsika-primary executable.
        If None, the path is looked up in the user's configfile
        ~/.corsika_primary.json
    """
    op = os.path
    if corsika_path is None:
        corsika_path = configfile.read()["corsika_primary"]

    corsika_path = op.abspath(corsika_path)
    steering_dict = copy.deepcopy(steering_dict)
    cherenkov_output_path = op.abspath(cherenkov_output_path)
    stdout_path = (
        stdout_path if stdout_path else cherenkov_output_path + ".stdout"
    )
    stderr_path = (
        stderr_path if stderr_path else cherenkov_output_path + ".stderr"
    )
    stdout_path = op.abspath(stdout_path)
    stderr_path = op.abspath(stderr_path)
    particle_output_path = op.abspath(particle_output_path)

    steering.assert_values(steering_dict=steering_dict)

    corsika_run_dir = op.dirname(corsika_path)

    with tempfile.TemporaryDirectory(prefix=tmp_dir_prefix) as tmp_dir:
        steering_card = steering.make_steering_card_str(
            steering_dict=steering_dict,
            output_path=cherenkov_output_path,
            parout_direct=tmp_dir,
        )
        primary_bytes = steering.primary_dicts_to_bytes(
            primary_dicts=steering_dict["primaries"]
        )

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

        if op.isfile(cherenkov_output_path):
            os.chmod(cherenkov_output_path, 0o664)

        datfilename = particles.dat.DAT_FILE_TEMPLATE.format(
            runnr=steering_dict["run"]["run_id"]
        )
        shutil.copy(os.path.join(tmp_dir, datfilename), particle_output_path)

    with open(stdout_path, "rt") as f:
        stdout_txt = f.read()
    assert testing.stdout_ends_with_end_of_run_marker(stdout_txt)

    return rc


def corsika_vanilla(
    steering_card,
    cherenkov_output_path,
    stdout_path=None,
    stderr_path=None,
    tmp_dir_prefix="corsika_primary_",
    corsika_path=None,
):
    """
    Call vanilla CORSIKA-7.56 and write Cherenkov-photons to cherenkov_output_path.

    This call is threadsafe, all execution takes place in a temproary copy
    of CORSIKA's run-directory.

    Parameters
    ----------
    steering_card : str
        The steering-card for vanilla CORSIKA-7.56.
    cherenkov_output_path : str
        Path to eventio-file with Cherenkov-photons.
    stdout_path : str
        Path to write CORSIKA's std-out to.
        If None: cherenkov_output_path + 'stdout'
    stderr_path : str
        Path to write CORSIKA's std-error to.
        If None: cherenkov_output_path + 'stderr'
    corsika_path : str (default: None)
        Path to corsika's executable in its 'run' directory.
        This is the vanilla corsika executable.
        If None, the path is looked up in the user's configfile
        ~/.corsika_primary.json
    """
    op = os.path
    if corsika_path is None:
        corsika_path = configfile.read()["corsika_vanilla"]

    corsika_path = op.abspath(corsika_path)
    cherenkov_output_path = op.abspath(cherenkov_output_path)
    steering_card = steering.overwrite_telfil_in_steering_card_str(
        card_str=steering_card, telfil=cherenkov_output_path
    )
    stdout_path = (
        stdout_path if stdout_path else cherenkov_output_path + ".stdout"
    )
    stderr_path = (
        stderr_path if stderr_path else cherenkov_output_path + ".stderr"
    )
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

        if op.isfile(cherenkov_output_path):
            os.chmod(cherenkov_output_path, 0o664)

    with open(stdout_path, "rt") as f:
        stdout_txt = f.read()
    assert testing.stdout_ends_with_end_of_run_marker(stdout_txt)

    return rc


class CorsikaPrimary:
    def __init__(
        self,
        steering_dict,
        stdout_path,
        stderr_path,
        particle_output_path,
        tmp_dir_prefix="corsika_primary_",
        corsika_path=None,
    ):
        """
        Inits a run-handle which can return the next event on demand.
        No output is written.

        This call is threadsafe, all execution takes place in a temproary copy
        of CORSIKA's run-directory.

        Parameters
        ----------
        steering_dict : dict
            The steering for the run and for each primary particle.
        stdout_path : str
            Path to write CORSIKA's std-out to.
        stderr_path : str
            Path to write CORSIKA's std-error to.
        particle_output_path : str
            Path to write the particle output to.
        corsika_path : str (default: None)
            Path to corsika's executable in its 'run' directory.
            This is the modified corsika-primary executable.
            If None, the path is looked up in the user's configfile
            ~/.corsika_primary.json
        """
        op = os.path
        if corsika_path is None:
            corsika_path = configfile.read()["corsika_primary"]

        self.corsika_path = op.abspath(corsika_path)
        self.steering_dict = copy.deepcopy(steering_dict)
        self.stdout_path = op.abspath(stdout_path)
        self.stderr_path = op.abspath(stderr_path)
        self.tmp_dir_prefix = str(tmp_dir_prefix)
        self.particle_output_path = str(particle_output_path)
        self.exit_ok = None

        steering.assert_values(steering_dict=self.steering_dict)

        self.tmp_dir_handle = tempfile.TemporaryDirectory(
            prefix=self.tmp_dir_prefix
        )
        self.tmp_dir = self.tmp_dir_handle.name

        self.cer_fifo_path = op.join(self.tmp_dir, "cer_fifo.tar")
        os.mkfifo(self.cer_fifo_path)

        self.tmp_corsika_run_dir = op.join(self.tmp_dir, "run")
        self.corsika_run_dir = op.dirname(self.corsika_path)

        shutil.copytree(
            self.corsika_run_dir, self.tmp_corsika_run_dir, symlinks=False
        )
        self.tmp_corsika_path = op.join(
            self.tmp_corsika_run_dir, op.basename(self.corsika_path)
        )

        self.steering_card = steering.make_steering_card_str(
            steering_dict=self.steering_dict,
            output_path=self.cer_fifo_path,
            parout_direct=self.tmp_dir,
        )
        assert self.steering_card[-1] == "\n", "Need newline to mark ending."

        self.tmp_particle_filename = particles.dat.DAT_FILE_TEMPLATE.format(
            runnr=self.steering_dict["run"]["run_id"]
        )
        self.tmp_particle_path = op.join(
            self.tmp_dir, self.tmp_particle_filename
        )

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

        self.cherenkov_reader = cherenkov.CherenkovEventTapeReader(
            path=self.cer_fifo_path
        )
        self.runh = self.cherenkov_reader.runh

    def close(self):
        self.cherenkov_reader.close()
        self.stdout.close()
        self.stderr.close()
        shutil.copy(self.tmp_particle_path, self.particle_output_path)

        if self.exit_ok is None:
            with open(self.stdout_path, "rt") as f:
                stdout = f.read()
            self.exit_ok = testing.stdout_ends_with_end_of_run_marker(stdout)

        self.tmp_dir_handle.cleanup()

    def __next__(self):
        cer_evth, cer_bunches = self.cherenkov_reader.__next__()
        return (cer_evth, cer_bunches)

    def __iter__(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def __repr__(self):
        out = "{:s}(path='{:s}', tmp_dir='{:s}')".format(
            self.__class__.__name__, self.corsika_path, self.tmp_dir
        )
        return out


def bunches_to_si_units(bunches):
    b = copy.deepcopy(bunches)
    b[:, I.BUNCH.X_CM] *= CM2M  # cm -> m
    b[:, I.BUNCH.Y_CM] *= CM2M  # cm -> m
    # b[:, I.BUNCH.CX_RAD]
    # b[:, I.BUNCH.CY_RAD]
    b[:, I.BUNCH.TIME_NS] *= 1e-9  # ns -> s
    b[:, I.BUNCH.EMISSOION_ALTITUDE_ASL_CM] *= CM2M  # cm -> m
    # b[:, I.BUNCH.BUNCH_SIZE_1] = bunches[:, I.BUNCH.BUNCH_SIZE_1]
    b[:, I.BUNCH.WAVELENGTH_NM] = (
        np.abs(b[:, I.BUNCH.WAVELENGTH_NM]) * 1e-9
    )  # nm -> m
    return b
