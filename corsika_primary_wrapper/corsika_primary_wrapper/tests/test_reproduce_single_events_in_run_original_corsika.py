import pytest
import os
import tempfile
import corsika_primary_wrapper as cpw
from corsika_primary_wrapper import testing as cpw_testing
import corsika_wrapper as cw
import subprocess
import simpleio
import numpy as np
import hashlib
import json
import copy
import shutil


@pytest.fixture()
def corsika_path(pytestconfig):
    return pytestconfig.getoption("corsika_path")


@pytest.fixture()
def merlict_eventio_converter(pytestconfig):
    return pytestconfig.getoption("merlict_eventio_converter")


@pytest.fixture()
def non_temporary_path(pytestconfig):
    return pytestconfig.getoption("non_temporary_path")


def hash_cherenkov_pools(card, tmp_dir, corsika_path, merlict_eventio_converter):
    os.makedirs(tmp_dir, exist_ok=True)
    run_eventio_path = os.path.join(tmp_dir, "eventio")
    run_simpelio_path = os.path.join(tmp_dir, "simpleio")
    run_hashes_path = os.path.join(tmp_dir, "cherenkov_pool_md5_hashes.csv")
    run_seeds_path = os.path.join(tmp_dir, "seeds.json")
    card_path = os.path.join(tmp_dir, "steering_card.txt")

    if not os.path.exists(run_hashes_path):
        with open(card_path, "wt") as f:
            f.write(card)

        cw.corsika(
            steering_card=cw.read_steering_card(card_path),
            output_path=run_eventio_path,
            save_stdout=True,
            corsika_path=corsika_path,
        )

        subprocess.call(
            [
                merlict_eventio_converter,
                "-i",
                run_eventio_path,
                "-o",
                run_simpelio_path,
            ]
        )

        run = simpleio.SimpleIoRun(run_simpelio_path)

        hashes_csv = ""
        event_seeds = {}
        for event_idx in range(len(run)):
            event = run[event_idx]
            evth = event.header.raw
            event_id = int(evth[cpw.I_EVTH_EVENT_NUMBER])
            bunches = cpw_testing.simpleio_bunches_to_array(
                bunches=event.cherenkov_photon_bunches
            )
            event_seeds[event_id] = cpw.event_seed_from_evth(evth=evth)
            h = hashlib.md5(bunches.tobytes()).hexdigest()
            hashes_csv += "{:06d},{:s}\n".format(event_id, h)

        with open(run_hashes_path, "wt") as f:
            f.write(hashes_csv)
        with open(run_seeds_path, "wt") as f:
            f.write(json.dumps(event_seeds, indent=4))

    with open(run_hashes_path, "rt") as f:
        hashes = {}
        for line in str.splitlines(f.read()):
            event_id_str, h_str = str.split(line, ",")
            hashes[int(event_id_str)] = h_str

    with open(run_seeds_path, "rt") as f:
        _event_seeds = json.loads(f.read())
        event_seeds = {}
        for key in _event_seeds:
            event_seeds[int(key)] = _event_seeds[key]

    return hashes, event_seeds


def test_reproduce_events_with_original_corsika(
    corsika_path,
    merlict_eventio_converter,
    non_temporary_path,
):
    assert os.path.exists(corsika_path)
    assert os.path.exists(merlict_eventio_converter)
    tmp_dir_handle = tempfile.TemporaryDirectory(prefix="corsika_")
    tmp_dir = non_temporary_path if non_temporary_path else tmp_dir_handle.name

    PARTICLES = {
        "gamma": {"particle_id": 1, "energy_GeV": 1.0},
        "electron": {"particle_id": 3, "energy_GeV": 1.0},
        "proton": {"particle_id": 14, "energy_GeV": 7.0},
        "helium": {"particle_id": 402, "energy_GeV": 12.0},
    }

    print("run reproduction")

    all_events_can_be_reproduced = True
    report = ""
    for pkey in PARTICLES:

        run_id = 1
        num_shower = 15
        particle_id = PARTICLES[pkey]["particle_id"]
        energy_GeV = PARTICLES[pkey]["energy_GeV"]
        chi_g_per_cm2 = 0.0
        obs_level_m = 2.3e3
        earth_magnetic_field_x_muT = 12.5
        earth_magnetic_field_z_muT = -25.9
        atmosphere_id = 10
        zenith_deg = 0.0
        azimuth_deg = 0.0
        telescope_sphere_radius_m = 1e4
        event_ids_to_reproduce = np.arange(1, num_shower + 1)


        card_template = "\n".join(
            [
                "RUNNR {:d}".format(run_id),
                "EVTNR {EVTNR:d}",
                "NSHOW {NSHOW:d}",
                "PRMPAR {:d}".format(particle_id),
                "ESLOPE 0",
                "ERANGE {:f} {:f}".format(energy_GeV, energy_GeV),
                "THETAP {:f} {:f}".format(zenith_deg, zenith_deg),
                "PHIP {:f} {:f}".format(azimuth_deg, azimuth_deg),
                "VIEWCONE 0 0",
                "SEED {seq1SEED:d} {seq1CALLS:d} {seq1BILLIONS:d}",
                "SEED {seq2SEED:d} {seq2CALLS:d} {seq2BILLIONS:d}",
                "SEED {seq3SEED:d} {seq3CALLS:d} {seq3BILLIONS:d}",
                "SEED {seq4SEED:d} {seq4CALLS:d} {seq4BILLIONS:d}",
                "OBSLEV {:f}".format(1e2 * obs_level_m),
                "FIXCHI {:f}".format(chi_g_per_cm2),
                "MAGNET {Bx:3.3e} {Bz:3.3e}".format(
                    Bx=earth_magnetic_field_x_muT,
                    Bz=earth_magnetic_field_z_muT,
                ),
                "ELMFLG T T",
                "MAXPRT 1",
                "PAROUT F F",
                "TELESCOPE 0 0 {:f} {:f}".format(
                    1e2 * telescope_sphere_radius_m * (-1),
                    1e2 * telescope_sphere_radius_m,
                ),
                "ATMOSPHERE {:d} T".format(atmosphere_id),
                "CWAVLG 250 700",
                "CSCAT 1 0 0",
                "CERQEF F T F",
                "CERSIZ 1.",
                "CERFIL F",
                "TSTART T",
                "EXIT",
            ]
        )

        full_card = card_template.format(
            EVTNR=1,
            NSHOW=num_shower,
            seq1SEED=1,
            seq1CALLS=0,
            seq1BILLIONS=0,
            seq2SEED=2,
            seq2CALLS=0,
            seq2BILLIONS=0,
            seq3SEED=3,
            seq3CALLS=0,
            seq3BILLIONS=0,
            seq4SEED=4,
            seq4CALLS=0,
            seq4BILLIONS=0,
        )

        full_dir = os.path.join(tmp_dir, pkey, "events_together")
        full_hashes, full_seeds = hash_cherenkov_pools(
            card=full_card,
            tmp_dir=full_dir,
            corsika_path=corsika_path,
            merlict_eventio_converter=merlict_eventio_converter,
        )

        repr_hashes = {}
        for event_id in event_ids_to_reproduce:
            seed = full_seeds[event_id]
            part_card = card_template.format(
                EVTNR=event_id,
                NSHOW=1,
                seq1SEED=seed[0]["SEED"],
                seq1CALLS=seed[0]["CALLS"],
                seq1BILLIONS=seed[0]["BILLIONS"],

                seq2SEED=seed[1]["SEED"],
                seq2CALLS=seed[1]["CALLS"],
                seq2BILLIONS=seed[1]["BILLIONS"],

                seq3SEED=seed[2]["SEED"],
                seq3CALLS=seed[2]["CALLS"],
                seq3BILLIONS=seed[2]["BILLIONS"],

                seq4SEED=seed[3]["SEED"],
                seq4CALLS=seed[3]["CALLS"],
                seq4BILLIONS=seed[3]["BILLIONS"],
            )

            part_dir = os.path.join(tmp_dir, pkey, "event_alone_{:06d}".format(event_id))
            part_hashes, part_seeds = hash_cherenkov_pools(
                card=part_card,
                tmp_dir=part_dir,
                corsika_path=corsika_path,
                merlict_eventio_converter=merlict_eventio_converter,
            )
            repr_hashes[event_id] = part_hashes[event_id]

        report += pkey  + "\n"
        report += "="*len(pkey) + "\n"
        report += "event-num.  reproduction\n"
        report += "------------------------\n"
        for event_id in event_ids_to_reproduce:
            fine = full_hashes[event_id] == repr_hashes[event_id]
            msg = "ok" if fine else "BAD"
            report += "  {: 3d}      ".format(event_id) + msg  + "\n"
            if not fine:
                all_events_can_be_reproduced = False
        report += "\n"

    with open(os.path.join(tmp_dir, "report.md"), "wt") as f:
        f.write(report)

    print(report)

    subprocess.call(
        [
            "tar",
            "-C",
            os.path.join(tmp_dir),
            "--exclude=simpleio",
            "--exclude=eventio",
            "--exclude=eventio.stderr",
            "-cvf",
            os.path.join(tmp_dir, "test.tar"),
            ".",
        ]
    )
    assert all_events_can_be_reproduced

    tmp_dir_handle.cleanup()
