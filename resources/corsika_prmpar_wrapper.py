import numpy as np
import tempfile
import os
import subprocess
import shutil
import io


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


def corsika(
    corsika_path,
    steering_card,
    primary_card,
    output_path,
    stdout_postfix=".stdout",
    stderr_postfix=".stderr",
    tmp_dir_prefix="corsika_prmpar_",
):
    """
    Call CORSIKA-primary mod

    Parameters
    ----------
        corsika_path            Path to corsika executable in its 'run'
                                directory.

        steering_card           String of lines seperated by newline.
                                Steers all constant properties of a run.

        primary_card            Bytes [f8, f8, f8, f8, f8, i4] for each
                                primary particle. The number of primaries will
                                overwrite NSHOW in steering_card.

        output_path             Path to output tape-archive.
    """
    op = os.path
    corsika_path = op.abspath(corsika_path)
    output_path = op.abspath(output_path)

    out_dirname = op.dirname(output_path)
    out_basename = op.basename(output_path)
    o_path = op.join(out_dirname, out_basename+stdout_postfix)
    e_path = op.join(out_dirname, out_basename+stderr_postfix)
    corsika_run_dir = op.dirname(corsika_path)
    num_primaries = len(primary_card)//NUM_BYTES_PER_PRIMARY

    with tempfile.TemporaryDirectory(prefix=tmp_dir_prefix) as tmp_dir:
        tmp_corsika_run_dir = op.join(tmp_dir, 'run')
        shutil.copytree(corsika_run_dir, tmp_corsika_run_dir, symlinks=False)
        tmp_corsika_path = op.join(
            tmp_corsika_run_dir,
            op.basename(corsika_path))

        primary_path = op.join(tmp_dir, "primary_card.f8f8f8f8f8i4")
        with open(primary_path, "wb") as f:
            f.write(primary_card)

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


EXAMPLE_STEERING_CARD = '\n'.join([
    'RUNNR 1',
    'EVTNR 1',
    'NSHOW 100',
    'ERANGE 0.25 1000',
    'OBSLEV 2347.0',
    'MAGNET 12.5 -25.9',
    'MAXPRT 1',
    'PAROUT F F',
    'ATMOSPHERE 10 T',
    'CWAVLG 250 700',
    'CERQEF F T F',
    'CERSIZ 1.',
    'CERFIL F',
    'TSTART T',
    'TELFIL out.tar',
    'PRMFIL explicit_primaries.f8f8f8f8f8i4',
    'EXIT',
])


def example_primaries(num_primaries=100, seed=0):
    np.random.seed(seed)
    primaries = []
    for i in range(num_primaries):
        prm = {}
        prm['particle'] = float(1)
        prm['energy'] = float(np.random.uniform(low=0.5, high=5, size=1))
        prm['theta'] = float(np.random.uniform(low=-0.1, high=.1, size=1))
        prm['phi'] = float(np.random.uniform(low=-0.1, high=.1, size=1))
        prm['depth'] = float(np.random.uniform(low=0.0, high=100.0, size=1))
        prm['seed'] = int(i + 1)
        primaries.append(prm)
    return primaries


def primaries_to_string(primaries):
    with io.BytesIO() as f:
        for prm in primaries:
            f.write(np.float64(prm['particle']).tobytes())
            f.write(np.float64(prm['energy']).tobytes())
            f.write(np.float64(prm['theta']).tobytes())
            f.write(np.float64(prm['phi']).tobytes())
            f.write(np.float64(prm['depth']).tobytes())
            f.write(np.int32(prm['seed']).tobytes())
        f.seek(0)
        return f.read()
