import pytest
import os
import tempfile
import corsika_primary_wrapper as cpw
import corsika_wrapper as cw
import numpy as np
from os import path as op
import subprocess

i4 = np.int32
i8 = np.int64
f8 = np.float64

@pytest.fixture()
def corsika_primary_path(pytestconfig):
    return pytestconfig.getoption("corsika_primary_path")


@pytest.fixture()
def corsika_path(pytestconfig):
    return pytestconfig.getoption("corsika_path")


@pytest.fixture()
def non_temporary_path(pytestconfig):
    return pytestconfig.getoption("non_temporary_path")


def test_low_energy_electron(
    corsika_primary_path,
    corsika_path,
    non_temporary_path,
):
    """
    I found televt_ not beeing called for some electron (id=3) or
    positron (id=2) events in chile site.
    This lead to televt_ not being called what lead to an error
    in the Cherenkov-buffer file.

    '''
    [ERROR] (iact.c:351: errno: Bad file descriptor)
    Can't ftell cherenkov_buffer
    '''

    AAMAIN/BOX3/EM/EGS4/SHOWER/ELECTR/TELEVT

    lables after televt() in ELECTR()

    500, 390, 420, 421

    primary exit label: 498

    Kill between:
    # 41444 "corsika.F"
    C  KILL UPWARD GOING PARTICLES
    IF ( W(NP) .LE. WCUT )
        IRETC = .FALSE.
        GOTO 420
    # 41484 "corsika.F"

    """
    assert os.path.exists(corsika_primary_path)

    num_shower = 10

    observation_level_asl_m = 5000
    earth_magnetic_field_x_muT = 20.815
    earth_magnetic_field_z_muT = -11.366
    atmosphere_id = 7

    particle_id = 2  # positron
    depth_g_per_cm2 = 0.0
    energy = 0.25
    zenith_deg = 45.0
    telescope_sphere_radius = 1e3

    ori_steering_card = "\n".join(
        [
            "RUNNR 1",
            "EVTNR 1",
            "NSHOW {:d}".format(num_shower),
            "PRMPAR {:d}".format(particle_id),
            "ESLOPE 0",
            "ERANGE {:f} {:f}".format(energy, energy),
            "THETAP {:f} {:f}".format(zenith_deg, zenith_deg),
            "PHIP {:f} {:f}".format(0.0, 0.0),
            "VIEWCONE 0 0",
            "SEED 1 0 0",
            "SEED 2 0 0",
            "SEED 3 0 0",
            "SEED 4 0 0",
            "OBSLEV {:f}".format(1e2 * observation_level_asl_m),
            "FIXCHI {:f}".format(depth_g_per_cm2),
            "MAGNET {Bx:3.3e} {Bz:3.3e}".format(
                Bx=earth_magnetic_field_x_muT, Bz=earth_magnetic_field_z_muT
            ),
            "ELMFLG T T",
            "MAXPRT 1",
            "PAROUT F F",
            "TELESCOPE 0 0 0 {:f}".format(1e2 * telescope_sphere_radius),
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

    tmp_prefix = "test_low_energy_electron_"
    with tempfile.TemporaryDirectory(prefix=tmp_prefix) as tmp_dir:
        if non_temporary_path != "":
            tmp_dir = op.join(non_temporary_path, tmp_prefix)
            os.makedirs(tmp_dir, exist_ok=True)

        # RUN ORIGINAL CORSIKA
        # --------------------
        # The original CORSIKA will fail to write valid output.
        ori_run_eventio_path = op.join(tmp_dir, "original_run.eventio")
        if not op.exists(ori_run_eventio_path):
            ori_card_path = op.join(tmp_dir, "original_steering_card.txt")
            with open(ori_card_path, "wt") as f:
                f.write(ori_steering_card)
            cw.corsika(
                steering_card=cw.read_steering_card(ori_card_path),
                output_path=ori_run_eventio_path,
                save_stdout=True,
                corsika_path=corsika_path,
            )

        with open(ori_run_eventio_path + ".stdout", "rt") as f:
            ori_stdout = f.read()
        ori_events_seeds = cpw._parse_random_seeds_from_corsika_stdout(
            stdout=ori_stdout
        )
        ori_num_bunches = cpw._parse_num_bunches_from_corsika_stdout(
            stdout=ori_stdout
        )

        # RUN MODIFIED CORSIKA
        # --------------------
        mod_steering_dict = {
            "run": {
                "run_id": i8(1),
                "event_id_of_first_event": i8(1),
                "observation_level_asl_m": f8(observation_level_asl_m),
                "earth_magnetic_field_x_muT": f8(earth_magnetic_field_x_muT),
                "earth_magnetic_field_z_muT": f8(earth_magnetic_field_z_muT),
                "atmosphere_id": i8(atmosphere_id),
                "energy_range": {"start_GeV": f8(0.2), "stop_GeV": f8(1.0)},
            },
            "primaries": [],
        }

        for idx in range(num_shower):
            prm = {
                "particle_id": f8(particle_id),
                "energy_GeV": f8(energy),
                "zenith_rad": f8(np.deg2rad(zenith_deg)),
                "azimuth_rad": f8(0.0),
                "depth_g_per_cm2": f8(depth_g_per_cm2),
                "random_seed": ori_events_seeds[idx],
            }
            mod_steering_dict["primaries"].append(prm)

        run_path = op.join(tmp_dir, "run.tar")
        cpw.corsika_primary(
            corsika_path=corsika_primary_path,
            steering_dict=mod_steering_dict,
            output_path=run_path,
            stdout_path=run_path + ".stdout",
        )
        with open(run_path + ".stdout", "rt") as f:
            stdout = f.read()
        assert cpw.stdout_ends_with_end_of_run_marker(stdout=stdout)

        run = cpw.Tario(run_path)
        for idx, event in enumerate(run):
            evth, bunches = event
            assert ori_num_bunches[idx] == bunches.shape[0]
