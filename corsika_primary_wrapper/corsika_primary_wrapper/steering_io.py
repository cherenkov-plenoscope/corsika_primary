import shutil
import io
import tarfile
import os
import numpy as np

"""
explicit_steerings is a dict mapping run_ids to
pair(steering_card, primary_bytes).

explicit_steerings can reproduce every shower bit by bit.
Unlike with json exports in plain text, here the binary primary_bytes are
stored explicitly.
"""


def write_explicit_steerings(explicit_steerings, path):
    with tarfile.open(path + ".tmp", "w") as tarfout:
        for run_id in explicit_steerings:
            expl = explicit_steerings[run_id]
            assert run_id == _get_run_id(steering_card=expl["steering_card"])
            _tar_write(
                tarfout=tarfout,
                path="{:06d}/steering_card.txt".format(run_id),
                payload=str.encode(expl["steering_card"], encoding="ascii"),
            )
            _tar_write(
                tarfout=tarfout,
                path="{:06d}/primary_bytes.bin".format(run_id),
                payload=expl["primary_bytes"],
            )
    shutil.move(path + ".tmp", path)


def read_explicit_steerings(path):
    out = {}
    with tarfile.open(path, "r") as tarfin:
        while True:
            tarinfo = tarfin.next()
            if tarinfo is None:
                break

            run_id_ste = int(os.path.dirname(tarinfo.name))
            basename = os.path.basename(tarinfo.name)
            assert basename == "steering_card.txt"
            steering_card = _tar_read_steering_card(
                tarfin=tarfin, tarinfo=tarinfo
            )
            assert run_id_ste == _get_run_id(steering_card=steering_card)

            tarinfo = tarfin.next()
            run_id_prm = int(os.path.dirname(tarinfo.name))
            basename = os.path.basename(tarinfo.name)
            assert basename == "primary_bytes.bin"
            primary_bytes = _tar_read_primary_bytes(
                tarfin=tarfin, tarinfo=tarinfo
            )
            assert run_id_ste == run_id_prm

            out[run_id_ste] = {
                "steering_card": steering_card,
                "primary_bytes": primary_bytes,
            }
    return out


def _tar_write(tarfout, path, payload):
    tarinfo = tarfile.TarInfo()
    tarinfo.name = path
    tarinfo.size = len(payload)
    with io.BytesIO() as f:
        f.write(payload)
        f.seek(0)
        tarfout.addfile(tarinfo=tarinfo, fileobj=f)


def _tar_write_steering_card(tarfout, path, steering_card):
    _tar_write(
        tarfout=tarfout,
        path=path,
        payload=str.encode(steering_card, encoding="ascii"),
    )


def _tar_write_primary_bytes(tarfout, path, primary_bytes):
    _tar_write(
        tarfout=tarfout, path=path, payload=primary_bytes,
    )


def _tar_read_steering_card(tarfin, tarinfo):
    b = tarfin.extractfile(tarinfo).read()
    return b.decode(encoding="ascii")


def _tar_read_primary_bytes(tarfin, tarinfo):
    return tarfin.extractfile(tarinfo).read()


def _get_run_id(steering_card):
    for line in str.splitlines(steering_card):
        if "RUNNR" in line:
            tmp = str.replace(line, "RUNNR", "")
            tmp = str.strip(tmp)
            return int(tmp)
    raise ValueError("No 'RUNNR' in steering_card.")

