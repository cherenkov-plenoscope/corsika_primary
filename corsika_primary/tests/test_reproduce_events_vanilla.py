import pytest
import os
import corsika_primary as cpw
import inspect
import subprocess
import numpy as np
import hashlib
import json
import copy
import shutil


@pytest.fixture()
def corsika_vanilla_path(pytestconfig):
    return pytestconfig.getoption("corsika_vanilla_path")


@pytest.fixture()
def merlict_eventio_converter(pytestconfig):
    return pytestconfig.getoption("merlict_eventio_converter")


@pytest.fixture()
def debug_dir(pytestconfig):
    return pytestconfig.getoption("debug_dir")


def hash_cherenkov_pools(
    steering_card, tmp_dir, corsika_vanilla_path, merlict_eventio_converter
):
    os.makedirs(tmp_dir, exist_ok=True)
    eventio_path = os.path.join(tmp_dir, "eventio")
    simpelio_path = os.path.join(tmp_dir, "simpleio")
    hashes_path = os.path.join(tmp_dir, "cherenkov_pool_md5_hashes.csv")
    seeds_path = os.path.join(tmp_dir, "seeds.csv")
    card_path = os.path.join(tmp_dir, "steering_card.txt")

    hashes = {}
    seeds = {}
    if not os.path.exists(hashes_path):
        with open(card_path, "wt") as f:
            f.write(steering_card)
        cpw.corsika_vanilla(
            corsika_path=corsika_vanilla_path,
            steering_card=steering_card,
            output_path=eventio_path,
            stdout_path=eventio_path + ".stdout",
            stderr_path=eventio_path + ".stderr",
        )
        cpw.testing.eventio_to_simpleio(
            merlict_eventio_converter=merlict_eventio_converter,
            eventio_path=eventio_path,
            simpleio_path=simpelio_path,
        )
        run = cpw.testing.SimpleIoRun(path=simpelio_path)

        for event in run:
            evth, bunches = event
            event_id = int(evth[cpw.I.EVTH.EVENT_NUMBER])
            hashes[event_id] = hashlib.md5(bunches.tobytes()).hexdigest()
            seeds[event_id] = cpw.random.seed.parse_seed_from_evth(evth)

        cpw.testing.write_hashes(path=hashes_path, hashes=hashes)
        cpw.testing.write_seeds(path=seeds_path, seeds=seeds)

    hashes = cpw.testing.read_hashes(path=hashes_path)
    seeds = cpw.testing.read_seeds(path=seeds_path)

    return hashes, seeds


def test_reproduce_events_vanilla(
    corsika_vanilla_path, merlict_eventio_converter, debug_dir,
):
    tmp = cpw.testing.TmpDebugDir(
        debug_dir=debug_dir,
        suffix=inspect.getframeinfo(inspect.currentframe()).function,
    )

    PARTICLES = {
        "gamma": {
            "particle_id": 1,
            "energy_GeV": 1.0,
            "expected_to_fail": set([]),
        },
        "electron": {
            "particle_id": 3,
            "energy_GeV": 1.0,
            "expected_to_fail": set([]),
        },
        "proton": {
            "particle_id": 14,
            "energy_GeV": 7.0,
            "expected_to_fail": set([13]),
        },
        "helium": {
            "particle_id": 402,
            "energy_GeV": 12.0,
            "expected_to_fail": set([2, 3, 15]),
        },
    }

    print("run reproduction")

    fails_as_expected = True
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
                "MAXPRT {NSHOW:d}",
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

        full_dir = os.path.join(tmp.name, pkey, "events_together")
        full_hashes, full_seeds = hash_cherenkov_pools(
            steering_card=full_card,
            tmp_dir=full_dir,
            corsika_vanilla_path=corsika_vanilla_path,
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

            part_dir = os.path.join(
                tmp.name, pkey, "event_alone_{:06d}".format(event_id)
            )
            part_hashes, part_seeds = hash_cherenkov_pools(
                steering_card=part_card,
                tmp_dir=part_dir,
                corsika_vanilla_path=corsika_vanilla_path,
                merlict_eventio_converter=merlict_eventio_converter,
            )
            repr_hashes[event_id] = part_hashes[event_id]

        report += pkey + "\n"
        report += "=" * len(pkey) + "\n"
        report += "| event-num. | reproduction |\n"
        report += "| ---------- | ------------ |\n"
        fails = []
        for event_id in event_ids_to_reproduce:
            fine = full_hashes[event_id] == repr_hashes[event_id]
            msg = "ok" if fine else "BAD"
            report += "| {: 3d} | ".format(event_id) + msg + " |\n"
            if not fine:
                fails.append(event_id)
        report += "\n"

        fails = set(fails)
        if PARTICLES[pkey]["expected_to_fail"] != fails:
            fails_as_expected = False

    with open(os.path.join(tmp.name, "report.md"), "wt") as f:
        f.write(report)

    print(report)

    subprocess.call(
        [
            "tar",
            "-C",
            os.path.join(tmp.name),
            "--exclude=simpleio",
            "--exclude=eventio",
            "--exclude=eventio.stderr",
            "-cvf",
            os.path.join(tmp.name, "test.tar"),
            ".",
        ]
    )
    assert fails_as_expected

    tmp.cleanup_when_no_debug()
