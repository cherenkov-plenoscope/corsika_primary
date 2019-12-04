import numpy as np
import tempfile
import os
import subprocess
import shutil
import io


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
            "random_seed": 0,
        },
        {
            "particle_id": 1,
            "energy_GeV": 1.52,
            "zenith_rad": 0.1,
            "azimuth_rad": 0.2,
            "depth_g_per_cm2": 3.6,
            "random_seed": 1,
        },
        {
            "particle_id": 1,
            "energy_GeV": 11.4,
            "zenith_rad": 0.1,
            "azimuth_rad": 0.25,
            "depth_g_per_cm2": 102.2,
            "random_seed": 2,
        },
    ],
}

NUM_BYTES_PER_PRIMARY = 5*8 + 4


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
            f.write(np.int32(prm['random_seed']).tobytes())
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

        primary_bytes   Bytes [f8, f8, f8, f8, f8, i4] for each
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
