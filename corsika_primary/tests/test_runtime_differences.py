import pytest
import os
import tempfile
import datetime
import corsika_primary as cpw
import inspect
import numpy as np

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


def test_runtime_differences(
    corsika_primary_path, corsika_vanilla_path, debug_dir,
):
    tmp = cpw.testing.TmpDebugDir(
        debug_dir=debug_dir,
        suffix=inspect.getframeinfo(inspect.currentframe()).function,
    )

    num_shower = 7
    particle_id = 3
    energy_GeV = 500
    starting_depth_g_per_cm2 = 0.0
    obs_level_asl_m = 2.3e3
    earth_magnetic_field_x_muT = 12.5
    earth_magnetic_field_z_muT = -25.9
    atmosphere_id = 10
    zenith_deg = 15.0
    azimuth_deg = 0.0
    telescope_sphere_radius = 36.0
    seed = cpw.random.seed.make_simple_seed(seed=3141)

    _S = "SEED"
    _C = "CALLS"
    _B = "BILLIONS"
    # RUN VANILLA CORSIKA
    # -------------------
    van_steering_card = "\n".join(
        [
            "RUNNR 1",
            "EVTNR 1",
            "NSHOW {:d}".format(num_shower),
            "PRMPAR {:d}".format(particle_id),
            "ESLOPE 0",
            "ERANGE {:f} {:f}".format(energy_GeV, energy_GeV),
            "THETAP {:f} {:f}".format(zenith_deg, zenith_deg),
            "PHIP {:f} {:f}".format(azimuth_deg, azimuth_deg),
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
            "OBSLEV {:f}".format(1e2 * obs_level_asl_m),
            "FIXCHI {:f}".format(starting_depth_g_per_cm2),
            "MAGNET {Bx:3.3e} {Bz:3.3e}".format(
                Bx=earth_magnetic_field_x_muT, Bz=earth_magnetic_field_z_muT,
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

    t_start_ori = datetime.datetime.now()
    van_run_path = os.path.join(tmp.name, "vanilla_run.eventio")
    if not os.path.exists(van_run_path):
        cpw.corsika_vanilla(
            corsika_path=corsika_vanilla_path,
            steering_card=van_steering_card,
            cherenkov_output_path=van_run_path,
            stdout_path=van_run_path + ".stdout",
            stderr_path=van_run_path + ".stderr",
        )
    t_end_ori = datetime.datetime.now()
    dt_ori = (t_end_ori - t_start_ori).total_seconds()
    print("vanilla: ", dt_ori)

    with open(van_run_path + ".stdout", "rt") as f:
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
            "observation_level_asl_m": f8(obs_level_asl_m),
            "earth_magnetic_field_x_muT": f8(earth_magnetic_field_x_muT),
            "earth_magnetic_field_z_muT": f8(earth_magnetic_field_z_muT),
            "atmosphere_id": i8(atmosphere_id),
            "energy_range": {
                "start_GeV": f8(energy_GeV * 0.9),
                "stop_GeV": f8(energy_GeV * 1.1),
            },
            "random_seed": seed,
        },
        "primaries": [],
    }

    for idx_primary in range(num_shower):
        prm = {
            "particle_id": f8(particle_id),
            "energy_GeV": f8(energy_GeV),
            "azimuth_rad": f8(np.deg2rad(azimuth_deg)),
            "zenith_rad": f8(np.deg2rad(zenith_deg)),
            "depth_g_per_cm2": f8(starting_depth_g_per_cm2),
        }
        mod_steering_dict["primaries"].append(prm)

    t_start_mod = datetime.datetime.now()
    mod_run_path = os.path.join(tmp.name, "modified_run")
    mod_cer_path = mod_run_path + ".cer.tar"
    mod_par_path = mod_run_path + ".par.dat"
    if not os.path.exists(mod_cer_path):
        cpw.corsika_primary(
            corsika_path=corsika_primary_path,
            steering_dict=mod_steering_dict,
            cherenkov_output_path=mod_cer_path,
            particle_output_path=mod_par_path,
        )
    t_end_mod = datetime.datetime.now()
    dt_mod = (t_end_mod - t_start_mod).total_seconds()

    print("modified: ", dt_mod)

    time_diff = np.abs(dt_mod - dt_ori)
    assert time_diff <= dt_ori, "modified runs >2 times longer than vanilla."

    tmp.cleanup_when_no_debug()
