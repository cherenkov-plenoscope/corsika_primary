import pytest
import os
import tempfile
import corsika_primary as cpw
import inspect
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
def corsika_vanilla_path(pytestconfig):
    return pytestconfig.getoption("corsika_vanilla_path")


@pytest.fixture()
def debug_dir(pytestconfig):
    return pytestconfig.getoption("debug_dir")


def test_low_energy_electron(
    corsika_primary_path, corsika_vanilla_path, debug_dir,
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
    tmp = cpw.testing.TmpDebugDir(
        debug_dir=debug_dir,
        suffix=inspect.getframeinfo(inspect.currentframe()).function,
    )

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
    seed = cpw.random.seed.make_simple_seed(seed=37)

    _S = "SEED"
    _C = "CALLS"
    _B = "BILLIONS"
    van_steering_card = "\n".join(
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
            "SEED {:d} {:d} {:d}".format(
                seed[0][_S], seed[0][_C], seed[0][_B]
            ),
            "SEED {:d} {:d} {:d}".format(
                seed[1][_S], seed[1][_C], seed[1][_B]
            ),
            "SEED {:d} {:d} {:d}".format(
                seed[2][_S], seed[2][_C], seed[2][_B]
            ),
            "SEED {:d} {:d} {:d}".format(
                seed[3][_S], seed[3][_C], seed[3][_B]
            ),
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
            "EXIT\n",
        ]
    )

    # RUN VANILLA CORSIKA
    # --------------------
    # The vanilla CORSIKA will fail to write valid output.
    van_run_path = op.join(tmp.name, "vanilla_run")
    van_run_eventio_path = van_run_path + ".eventio"
    if not op.exists(van_run_eventio_path):
        cpw.corsika_vanilla(
            corsika_path=corsika_vanilla_path,
            steering_card=van_steering_card,
            output_path=van_run_eventio_path,
            stdout_path=van_run_eventio_path + ".stdout",
            stderr_path=van_run_eventio_path + ".stderr",
        )

    with open(van_run_eventio_path + ".stdout", "rt") as f:
        van_stdout = f.read()
    van_events_seeds = cpw.testing.parse_random_seeds_from_corsika_stdout(
        stdout=van_stdout
    )
    van_num_bunches = cpw.testing.parse_num_bunches_from_corsika_stdout(
        stdout=van_stdout
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
            "random_seed": seed,
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
        }
        mod_steering_dict["primaries"].append(prm)

    mod_run_path = op.join(tmp.name, "modified_run.tar")
    if not op.exists(mod_run_path):
        cpw.corsika_primary(
            corsika_path=corsika_primary_path,
            steering_dict=mod_steering_dict,
            output_path=mod_run_path,
            stdout_path=mod_run_path + ".stdout",
        )
    with open(mod_run_path + ".stdout", "rt") as f:
        stdout = f.read()
    assert cpw.testing.stdout_ends_with_end_of_run_marker(stdout=stdout)

    run = cpw.event_tape.EventTapeReader(mod_run_path)
    for idx, event in enumerate(run):
        evth, cer_reader = event
        bunches = np.vstack([b for b in cer_reader])
        assert van_num_bunches[idx] == bunches.shape[0]

    tmp.cleanup_when_no_debug()
