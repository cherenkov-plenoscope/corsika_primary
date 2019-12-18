import numpy as np
import tempfile
import os
import subprocess
import shutil
import io
import tarfile
import struct


def _simple_seed(seed):
    return [
        {"SEED": seed, "CALLS": 0, "BILLIONS": 0},
        {"SEED": seed+1, "CALLS": 0, "BILLIONS": 0},
        {"SEED": seed+2, "CALLS": 0, "BILLIONS": 0},
        {"SEED": seed+3, "CALLS": 0, "BILLIONS": 0}]


EXAMPLE_STEERING_DICT = {
    "run": {
        "run_id": 1,
        "event_id_of_first_event": 1,
        "observation_level_altitude_asl": 2300,
        "earth_magnetic_field_x_muT": 12.5,
        "earth_magnetic_field_z_muT": -25.9,
        "atmosphere_id": 10,
    },
    "primaries": [
        {
            "particle_id": 1,
            "energy_GeV": 1.32,
            "zenith_rad": 0.0,
            "azimuth_rad": 0.0,
            "depth_g_per_cm2": 0.0,
            "random_seed": _simple_seed(0),
        },
        {
            "particle_id": 1,
            "energy_GeV": 1.52,
            "zenith_rad": 0.1,
            "azimuth_rad": 0.2,
            "depth_g_per_cm2": 3.6,
            "random_seed": _simple_seed(1),
        },
        {
            "particle_id": 1,
            "energy_GeV": 11.4,
            "zenith_rad": 0.1,
            "azimuth_rad": 0.25,
            "depth_g_per_cm2": 102.2,
            "random_seed": _simple_seed(2),
        },
    ],
}

NUM_BYTES_PER_PRIMARY = 5*8 + 12*4
NUM_BYTES_PER_BUNCH = len(["x", "y", "cx", "cy", "t", "zem", "wvl", "size"])*4
IX = 0
IY = 1
ICX = 2
ICY = 3
ITIME = 4
IZEM = 5
IBSIZE = 6
IWVL = 7


def _overwrite_steering_card(
    steering_card,
    output_path,
    primary_path,
    num_shower,
):
    lines = []
    for line in steering_card.splitlines():
        key = line.split(' ')[0]
        if key not in ["EXIT", "TELFIL", "PRMFIL", "NSHOW"]:
            lines.append(line)
    lines.append("NSHOW {:d}".format(num_shower))
    lines.append("PRMFIL {:s}".format(primary_path))
    lines.append("TELFIL {:s}".format(output_path))
    lines.append("EXIT")
    return "\n".join(lines)


def _primaries_to_bytes(primaries):
    with io.BytesIO() as f:
        for prm in primaries:
            f.write(np.float64(prm['particle_id']).tobytes())
            f.write(np.float64(prm['energy_GeV']).tobytes())
            f.write(np.float64(prm['zenith_rad']).tobytes())
            f.write(np.float64(prm['azimuth_rad']).tobytes())
            f.write(np.float64(prm['depth_g_per_cm2']).tobytes())
            for nseq in range(4):
                for key in ["SEED", "CALLS", "BILLIONS"]:
                    f.write(np.int32(prm['random_seed'][nseq][key]).tobytes())
        f.seek(0)
        return f.read()


def _dict_to_card_and_bytes(steering_dict):
    run = steering_dict["run"]
    primary_binary = _primaries_to_bytes(steering_dict["primaries"])
    _energies = [prm["energy_GeV"] for prm in steering_dict["primaries"]]

    corsika_card = '\n'.join([
        'RUNNR {:d}'.format(run["run_id"]),
        'EVTNR {:d}'.format(run["event_id_of_first_event"]),
        'ERANGE {e_min:f} {e_max:f}'.format(
            e_min=np.min(_energies),
            e_max=np.max(_energies)),
        'OBSLEV {:f}'.format(1e2*run["observation_level_altitude_asl"]),
        'MAGNET {x:f} {z:f}'.format(
            x=run["earth_magnetic_field_x_muT"],
            z=run["earth_magnetic_field_z_muT"]),
        'MAXPRT 1',
        'PAROUT F F',
        'ATMOSPHERE {:d} T'.format(run["atmosphere_id"]),
        'CWAVLG 250 700',
        'CERQEF F T F',
        'CERSIZ 1.',
        'CERFIL F',
        'TSTART T',
        'NSHOW {:d}'.format(len(steering_dict["primaries"])),
        'PRMFIL primary_bytes.f8f8f8f8f8i4',
        'TELFIL run.tar',
        'EXIT'])
    return corsika_card, primary_binary


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
        tmp_dir_prefix=tmp_dir_prefix)


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
    o_path = op.join(out_dirname, out_basename+stdout_postfix)
    e_path = op.join(out_dirname, out_basename+stderr_postfix)
    corsika_run_dir = op.dirname(corsika_path)
    num_primaries = len(primary_bytes)//NUM_BYTES_PER_PRIMARY

    with tempfile.TemporaryDirectory(prefix=tmp_dir_prefix) as tmp_dir:
        tmp_corsika_run_dir = op.join(tmp_dir, 'run')
        shutil.copytree(corsika_run_dir, tmp_corsika_run_dir, symlinks=False)
        tmp_corsika_path = op.join(
            tmp_corsika_run_dir,
            op.basename(corsika_path))

        primary_path = op.join(tmp_dir, "primary_bytes.f8f8f8f8f8i4")
        with open(primary_path, "wb") as f:
            f.write(primary_bytes)

        steering_card = _overwrite_steering_card(
            steering_card=steering_card,
            output_path=output_path,
            primary_path=primary_path,
            num_shower=num_primaries)

        steering_card_pipe, pwrite = os.pipe()
        os.write(pwrite, str.encode(steering_card))
        os.close(pwrite)

        with open(o_path, 'w') as stdout, open(e_path, 'w') as stderr:
            rc = subprocess.call(
                tmp_corsika_path,
                stdin=steering_card_pipe,
                stdout=stdout,
                stderr=stderr,
                cwd=tmp_corsika_run_dir)

        if op.isfile(output_path):
            os.chmod(output_path, 0o664)

    return rc


RUNH_MARKER_FLOAT32 = struct.unpack('f', "RUNH".encode())[0]
EVTH_MARKER_FLOAT32 = struct.unpack('f', "EVTH".encode())[0]


class Tario:
    def __init__(self, path):
        self.path = path
        self.tar = tarfile.open(path, 'r:*')

        runh_tar = self.tar.next()
        runh_bin = self.tar.extractfile(runh_tar).read()
        self.runh = np.frombuffer(runh_bin, dtype=np.float32)
        assert self.runh[0] == RUNH_MARKER_FLOAT32
        self.num_events_read = 0

    def __next__(self):
        evth_tar = self.tar.next()
        bunches_tar = self.tar.next()
        if evth_tar is None:
            raise StopIteration

        evth_number = int(evth_tar.name[0: 9])
        bunches_number = int(bunches_tar.name[0: 9])
        assert evth_number == bunches_number

        evth_bin = self.tar.extractfile(evth_tar).read()
        evth = np.frombuffer(evth_bin, dtype=np.float32)
        assert evth[0] == EVTH_MARKER_FLOAT32
        assert int(np.round(evth[1])) == evth_number

        bunches_bin = self.tar.extractfile(bunches_tar).read()
        bunches = np.frombuffer(bunches_bin, dtype=np.float32)
        num_bunches = bunches.shape[0]//(8)

        self.num_events_read += 1
        return (evth, np.reshape(bunches, newshape=(num_bunches, 8)))

    def __iter__(self):
        return self

    def __exit__(self):
        self.tar.close()

    def __repr__(self):
        out = "{:s}(path='{:s}', read={:d})".format(
            self.__class__.__name__,
            self.path,
            self.num_events_read)
        return out


NUM_RANDOM_SEQUENCES = 4


def _parse_random_seeds_from_corsika_stdout(stdout):
    events = []
    MARKER = " AND RANDOM NUMBER GENERATOR AT BEGIN OF EVENT :"
    lines = stdout.split("\n")
    idx = 0
    while idx < len(lines):
        if MARKER in lines[idx]:
            _seeds = [None]*NUM_RANDOM_SEQUENCES
            _calls = [None]*NUM_RANDOM_SEQUENCES
            _billions = [None]*NUM_RANDOM_SEQUENCES
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
                        "BILLIONS": _billions[seq]
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
            work_line = lines[ll][len(marker):-1]
            pos_2nd_in = work_line.find("in")
            work_line = work_line[pos_2nd_in + 2: -len("bunch") -1]
            nums.append(int(float(work_line)))
    return nums


def _evth_marker(evth): return evth[1-1]


def _evth_event_number(evth): return evth[2-1]


def _evth_particle_id(evth): return evth[3-1]


def _evth_total_energy_GeV(evth): return evth[4-1]


def _evth_starting_depth_g_per_cm2(evth): return evth[5-1]


def _evth_number_of_first_target_if_fixed(evth): return evth[6-1]


def _evth_z_coordinate_of_first_interaction_cm(evth): return evth[7-1]


def _evth_px_momentum_in_x_direction_GeV_per_c(evth): return evth[8-1]


def _evth_py_momentum_in_y_direction_GeV_per_c(evth): return evth[9-1]


def _evth_pz_momentum_in_z_direction_GeV_per_c(evth): return evth[10-1]


def _evth_zenith_rad(evth): return evth[11-1]


def _evth_azimuth_rad(evth): return evth[12-1]


def _evth_number_of_different_random_number_sequence(evth): return evth[13-1]


def _evth_run_number(evth): return evth[44-1]


def _evth_date_of_begin_run_yymmdd(evth): return evth[45-1]


def _evth_version_of_program(evth): return evth[46-1]


def _evth_number_of_observation_levels(evth): return evth[47-1]


def _evth_height_of_level_1_cm(evth): return evth[48-1]


def _evth_Cherenkov_bunch_size(evth): return evth[85-1]


def _evth_angle_between_x_direction_and_magnetic_north_rad(evth):
    return evth[93-1]


def _evth_Cherenkov_wavelength_start_nm(evth): return evth[96-1]


def _evth_Cherenkov_wavelength_stop_nm(evth): return evth[97-1]


def _evth_number_reuses(evth): return evth[98-1]


def _evth_integer_seed_of_sequence(evth, i): return evth[11+(3*i)-1]


def _evth_number_offsets_random_calls_mod_million(evth, i):
    return evth[21+(3*i)-1]


def _evth_number_offsets_random_calls_divide_million(evth, i):
    return evth[31+(3*i)-1]


def _runh_number_events(runh):
    return runh[93-1]
