import pytest
import os
import tempfile
import datetime
import corsika_primary_wrapper as cpw
import corsika_wrapper as cw
import numpy as np


@pytest.fixture()
def corsika_primary_path(pytestconfig):
    return pytestconfig.getoption("corsika_primary_path")


@pytest.fixture()
def corsika_path(pytestconfig):
    return pytestconfig.getoption("corsika_path")


@pytest.fixture()
def non_temporary_path(pytestconfig):
    return pytestconfig.getoption("non_temporary_path")


def test_runtime_differences(
    corsika_primary_path,
    corsika_path,
    non_temporary_path,
):
    assert(os.path.exists(corsika_primary_path))
    assert(os.path.exists(corsika_path))

    np.random.seed(0)

    num_shower = 7
    particle_id = 3
    energy_GeV = 500
    starting_depth_g_per_cm2 = 0.0
    obs_level_asl_m = 2.3e3
    earth_magnetic_field_x_muT = 12.5
    earth_magnetic_field_z_muT = -25.9
    atmosphere_id = 10
    zenith_deg = 15.
    azimuth_deg = 0.
    telescope_sphere_radius = 36.0

    tmp_prefix = "test_runtime_"
    with tempfile.TemporaryDirectory(prefix=tmp_prefix) as tmp_dir:
        if non_temporary_path != "":
            tmp_dir = os.path.join(
                non_temporary_path,
                tmp_prefix)
            os.makedirs(tmp_dir, exist_ok=True)

        # RUN ORIGINAL CORSIKA
        # --------------------
        ori_steering_card = "\n".join([
            "RUNNR 1",
            "EVTNR 1",
            "NSHOW {:d}".format(num_shower),
            "PRMPAR {:d}".format(particle_id),
            "ESLOPE 0",
            "ERANGE {:f} {:f}".format(energy_GeV, energy_GeV),
            "THETAP {:f} {:f}".format(zenith_deg, zenith_deg),
            "PHIP {:f} {:f}".format(azimuth_deg, azimuth_deg),
            "VIEWCONE 0 0",
            "SEED 1 0 0",
            "SEED 2 0 0",
            "SEED 3 0 0",
            "SEED 4 0 0",
            "OBSLEV {:f}".format(1e2*obs_level_asl_m),
            'FIXCHI {:f}'.format(starting_depth_g_per_cm2),
            'MAGNET {Bx:3.3e} {Bz:3.3e}'.format(
                Bx=earth_magnetic_field_x_muT,
                Bz=earth_magnetic_field_z_muT),
            'ELMFLG T T',
            'MAXPRT 1',
            'PAROUT F F',
            'TELESCOPE 0 0 0 {:f}'.format(1e2*telescope_sphere_radius),
            'ATMOSPHERE {:d} T'.format(atmosphere_id),
            'CWAVLG 250 700',
            'CSCAT 1 0 0',
            'CERQEF F T F',
            'CERSIZ 1.',
            'CERFIL F',
            'TSTART T',
            'EXIT',
        ])

        t_start_ori = datetime.datetime.now()
        ori_run_path = os.path.join(tmp_dir, "original_run.eventio")
        if not os.path.exists(ori_run_path):
            ori_card_path = os.path.join(
                tmp_dir,
                "original_steering_card.txt")
            with open(ori_card_path, "wt") as f:
                f.write(ori_steering_card)
            cw.corsika(
                steering_card=cw.read_steering_card(ori_card_path),
                output_path=ori_run_path,
                save_stdout=True,
                corsika_path=corsika_path)
        t_end_ori = datetime.datetime.now()
        dt_ori = (t_end_ori - t_start_ori).total_seconds()
        print('ori: ', dt_ori)

        with open(ori_run_path+".stdout", "rt") as f:
            ori_stdout = f.read()
        ori_events_seeds = cpw._parse_random_seeds_from_corsika_stdout(
            stdout=ori_stdout)
        ori_num_bunches = cpw._parse_num_bunches_from_corsika_stdout(
            stdout=ori_stdout)

        # RUN MODIFIED CORSIKA
        # --------------------
        mod_steering_dict = {
            "run": {
                "run_id": 1,
                "event_id_of_first_event": 1,
                "observation_level_asl_m": obs_level_asl_m,
                "earth_magnetic_field_x_muT": earth_magnetic_field_x_muT,
                "earth_magnetic_field_z_muT": earth_magnetic_field_z_muT,
                "atmosphere_id": atmosphere_id,
            },
            "primaries": []}

        for idx_primary in range(num_shower):
            prm = {
                "particle_id": particle_id,
                "energy_GeV": energy_GeV,
                "azimuth_rad": np.deg2rad(azimuth_deg),
                "zenith_rad": np.deg2rad(zenith_deg),
                "depth_g_per_cm2": starting_depth_g_per_cm2,
                "random_seed": ori_events_seeds[idx_primary],
            }
            mod_steering_dict["primaries"].append(prm)

        t_start_mod = datetime.datetime.now()
        mod_run_path = os.path.join(tmp_dir, "modified_run.tar")
        if not os.path.exists(mod_run_path):
            cpw.corsika_primary(
                corsika_path=corsika_primary_path,
                steering_dict=mod_steering_dict,
                output_path=mod_run_path)
        t_end_mod = datetime.datetime.now()
        dt_mod = (t_end_mod - t_start_mod).total_seconds()
    print('mod: ', dt_mod)

    time_diff = np.abs(dt_mod - dt_ori)
    assert time_diff <= dt_ori, 'mod runs over 2 times longer than ori.'
