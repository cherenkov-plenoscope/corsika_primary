import pytest
import os
import tempfile
import corsika_primary_wrapper as cpw
import corsika_wrapper as cw
import simpleio
import numpy as np
import subprocess
import pandas as pd


@pytest.fixture()
def corsika_primary_path(pytestconfig):
    return pytestconfig.getoption("corsika_primary_path")


@pytest.fixture()
def corsika_path(pytestconfig):
    return pytestconfig.getoption("corsika_path")


@pytest.fixture()
def merlict_eventio_converter(pytestconfig):
    return pytestconfig.getoption("merlict_eventio_converter")

IX = 0
IY = 1
ICX = 2
ICY = 3
ITIME = 4
IZEM = 5
IBSIZE = 6
IWVL = 7

def equal(a, b, absolute_margin=1e-6):
    return np.abs(a - b) < absolute_margin


def _tario_bunches_to_array(bunches):
    b = np.zeros(shape=bunches.shape, dtype=np.float32)
    b[:, IX] = bunches[:, IX]*1e-2 # cm -> m
    b[:, IY] = bunches[:, IY]*1e-2 # cm -> m
    b[:, ICX] = bunches[:, ICX]
    b[:, ICY] = bunches[:, ICY]
    b[:, ITIME] = bunches[:, ITIME]*1e-9 # ns -> s
    b[:, IZEM] = bunches[:, IZEM]*1e-2 # cm -> m
    b[:, IBSIZE] = bunches[:, IBSIZE]
    b[:, IWVL] = np.abs(bunches[:, IWVL])*1e-9 # nm -> m
    return b

def _simpleio_bunches_to_array(bunches):
    num_bunches = bunches.x.shape[0]
    b = np.zeros(shape=(num_bunches, 8), dtype=np.float32)
    b[:, IX] = bunches.x
    b[:, IY] = bunches.y
    b[:, ICX] = bunches.cx
    b[:, ICY] = bunches.cy
    b[:, ITIME] = bunches.arrival_time_since_first_interaction
    b[:, IZEM] = bunches.emission_height
    b[:, IBSIZE] = bunches.probability_to_reach_observation_level
    b[:, IWVL] = np.abs(bunches.wavelength)
    return b


bsize_bin_edges = np.linspace(0, 1, 101)
wvl_bin_edges = np.linspace(250e-9, 700e-9, 21)
zem_bin_edges = np.linspace(2e3, 52e3, 21)
xy_bin_edges = np.linspace(-10e3, 10e3, 20+1)
cxcy_bin_edges = np.linspace(-np.deg2rad(20), np.deg2rad(20), 40+1)
time_bin_edges = np.linspace(3e-4, 5e-4, 21)


def _append_bunch_statistics(stats, bunches):
    num_bunches = bunches.shape[0]
    stats["x_median"].append(np.median(bunches[:, IX]))
    stats["x_std"].append(np.std(bunches[:, IX]))
    stats["x_hist"].append(
        np.histogram(bunches[:, IX], bins=xy_bin_edges)[0]/num_bunches)

    stats["y_median"].append(np.median(bunches[:, IY]))
    stats["y_std"].append(np.std(bunches[:, IY]))
    stats["y_hist"].append(
        np.histogram(bunches[:, IY], bins=xy_bin_edges)[0]/num_bunches)

    stats["cx_median"].append(np.median(bunches[:, ICX]))
    stats["cx_std"].append(np.std(bunches[:, ICX]))
    stats["cx_hist"].append(
        np.histogram(bunches[:, ICX], bins=cxcy_bin_edges)[0]/num_bunches)

    stats["cy_median"].append(np.median(bunches[:, ICY]))
    stats["cy_std"].append(np.std(bunches[:, ICY]))
    stats["cy_hist"].append(
        np.histogram(bunches[:, ICY], bins=cxcy_bin_edges)[0]/num_bunches)

    stats["time_median"].append(np.median(bunches[:, ITIME]))
    stats["time_std"].append(np.std(bunches[:, ITIME]))
    stats["time_hist"].append(
        np.histogram(bunches[:, ITIME], bins=time_bin_edges)[0]/num_bunches)

    stats["zem_median"].append(np.median(bunches[:, IZEM]))
    stats["zem_std"].append(np.std(bunches[:, IZEM]))
    stats["zem_hist"].append(
        np.histogram(bunches[:, IZEM], bins=zem_bin_edges)[0]/num_bunches)

    stats["bsize_median"].append(np.median(bunches[:, IBSIZE]))
    stats["bsize_std"].append(np.std(bunches[:, IBSIZE]))
    stats["bsize_hist"].append(np.histogram(
        bunches[:, IBSIZE], bins=bsize_bin_edges)[0]/num_bunches)

    stats["wvl_median"].append(np.median(bunches[:, IWVL]))
    stats["wvl_std"].append(np.std(bunches[:, IWVL]))
    stats["wvl_hist"].append(
        np.histogram(bunches[:, IWVL], bins=wvl_bin_edges)[0]/num_bunches)

    stats["num_bunches"].append(bunches.shape[0])
    return stats

KEYS = ['x', 'y', 'cx', 'cy', 'time', 'zem', 'bsize', 'wvl']

def _init_stats():
    stats = {}
    stats['num_bunches'] = []
    for n in KEYS:
        stats[n+"_median"] = []
        stats[n+"_std"] = []
        stats[n+"_hist"] = []
    return stats


def test_original_vs_moddified(
    corsika_primary_path,
    corsika_path,
    merlict_eventio_converter
):
    """
    Check whether the moddifief CORSIKA can reproduce the statistics of the
    original CORSIKA within the parameter-space both versions can access.
    """
    assert(os.path.exists(corsika_primary_path))
    assert(os.path.exists(corsika_path))
    assert(os.path.exists(merlict_eventio_converter))

    np.random.seed(0)

    num_shower = 1024

    chi_g_per_cm2 = 0.0
    obs_level = 2.3e3
    earth_magnetic_field_x_muT = 12.5
    earth_magnetic_field_z_muT = -25.9
    atmosphere_id = 10
    zenith_deg = 0.
    azimuth_deg = 0.

    cfg = {
        "gamma": {"id": 1, "energy": 1.337},
        "electron": {"id": 3, "energy": 1.337},
        "proton": {"id": 14, "energy": 6.5},
    }

    run = 0
    for particle in cfg:

        ori_steering_card = "\n".join([
            "RUNNR 1",
            "EVTNR 1",
            "NSHOW {:d}".format(num_shower),
            "PRMPAR {:d}".format(cfg[particle]["id"]),
            "ESLOPE 0",
            "ERANGE {:f} {:f}".format(
                cfg[particle]["energy"],
                cfg[particle]["energy"]),
            "THETAP {:f} {:f}".format(zenith_deg, zenith_deg),
            "PHIP {:f} {:f}".format(azimuth_deg, azimuth_deg),
            "VIEWCONE 0 0",
            "SEED 1 0 0",
            "SEED 2 0 0",
            "SEED 3 0 0",
            "SEED 4 0 0",
            "OBSLEV {:f}".format(1e2*obs_level),
            'FIXCHI {:f}'.format(chi_g_per_cm2),
            'MAGNET {Bx:3.3e} {Bz:3.3e}'.format(
                Bx=earth_magnetic_field_x_muT,
                Bz=earth_magnetic_field_z_muT),
            'ELMFLG T T',
            'MAXPRT 1',
            'PAROUT F F',
            'TELESCOPE 0.0 0.0 0.0 1e6',
            'ATMOSPHERE {:d} T'.format(atmosphere_id),
            'CWAVLG 250 700',
            'CSCAT 1 0 0',
            'CERQEF F T F',
            'CERSIZ 1.',
            'CERFIL F',
            'TSTART T',
            'EXIT',
        ])

        mod_steering_dict = {
            "run": {
                "run_id": 1,
                "event_id_of_first_event": 1,
                "observation_level_altitude_asl": obs_level,
                "earth_magnetic_field_x_muT": earth_magnetic_field_x_muT,
                "earth_magnetic_field_z_muT": earth_magnetic_field_z_muT,
                "atmosphere_id": atmosphere_id,},
            "primaries": []}

        for idx_primary in range(num_shower):
            prm = {
                "particle_id": cfg[particle]["id"],
                "energy_GeV": cfg[particle]["energy"],
                "zenith_rad": np.deg2rad(zenith_deg),
                "azimuth_rad": np.deg2rad(azimuth_deg),
                "depth_g_per_cm2": chi_g_per_cm2,
                "random_seed": idx_primary + 1,
            }
            mod_steering_dict["primaries"].append(prm)

        with tempfile.TemporaryDirectory(prefix="test_primary_") as tmp_dir:
            tmp_dir = "/home/sebastian/Desktop/test_primary"
            os.makedirs(tmp_dir, exist_ok=True)

            mod_run_path = os.path.join(tmp_dir, "run_{:d}.tar".format(run))
            cpw.corsika_primary(
                corsika_path=corsika_primary_path,
                steering_dict=mod_steering_dict,
                output_path=mod_run_path)

            ori_card_path = os.path.join(
                tmp_dir,
                "original_steering_card_{:d}.txt".format(run))
            with open(ori_card_path, "wt") as f:
                f.write(ori_steering_card)
            ori_run_eventio_path = os.path.join(
                tmp_dir,
                "run_{:d}.eventio".format(run))
            cw.corsika(
                steering_card=cw.read_steering_card(ori_card_path),
                output_path=ori_run_eventio_path,
                save_stdout=True,
                corsika_path=corsika_path)
            ori_run_path = os.path.join(
                tmp_dir,
                "run_{:d}.simpleio".format(run))
            subprocess.call([
                merlict_eventio_converter,
                "-i", ori_run_eventio_path,
                "-o", ori_run_path])
            mod_run = cpw.Tario(mod_run_path)
            ori_run = simpleio.SimpleIoRun(ori_run_path)

            ori_stats = _init_stats()
            mod_stats = _init_stats()
            for evt_idx in range(num_shower):
                mod_evth, _mod_bunches = next(mod_run)
                mod_bunches = _tario_bunches_to_array(_mod_bunches)
                _ori_event = ori_run[evt_idx]
                ori_evth = _ori_event.header.raw
                ori_bunches = _simpleio_bunches_to_array(
                    _ori_event.cherenkov_photon_bunches)
                ori_stats = _append_bunch_statistics(ori_stats, ori_bunches)
                mod_stats = _append_bunch_statistics(mod_stats, mod_bunches)

                assert equal(
                    cpw._evth_zenith_rad(mod_evth),
                    np.deg2rad(zenith_deg),
                    1e-6)
                assert equal(
                    cpw._evth_zenith_rad(ori_evth),
                    np.deg2rad(zenith_deg),
                    1e-6)

                assert equal(
                    cpw._evth_particle_id(mod_evth),
                    cfg[particle]["id"],
                    1e-6)
                assert equal(
                    cpw._evth_particle_id(ori_evth),
                    cfg[particle]["id"],
                    1e-6)

                assert equal(
                    cpw._evth_total_energy_GeV(mod_evth),
                    cfg[particle]["energy"],
                    1e-6)
                assert equal(
                    cpw._evth_total_energy_GeV(ori_evth),
                    cfg[particle]["energy"],
                    1e-6)

                assert equal(
                    cpw._evth_azimuth_rad(mod_evth),
                    np.deg2rad(azimuth_deg),
                    1e-6)
                assert equal(
                    cpw._evth_azimuth_rad(ori_evth),
                    np.deg2rad(azimuth_deg),
                    1e-6)

            for key in KEYS:
                for met in ["_median", "_std", "_hist"]:
                    ori_stats[key+met] = np.sum(
                        ori_stats[key+met], axis=0)/num_shower
                    mod_stats[key+met] = np.sum(
                        mod_stats[key+met], axis=0)/num_shower

            relative_uncertainty = 1/np.sqrt(num_shower)

            for k in KEYS:
                print("\n")
                print(k)
                print("median:", ori_stats[k+"_median"], mod_stats[k+"_median"])
                print("std:", ori_stats[k+"_std"], mod_stats[k+"_std"])
                print("hist ori, mod:")
                for ii in range(ori_stats[k+"_hist"].shape[0]):
                    print("{:.2f} {:.2f}".format(
                        ori_stats[k+"_hist"][ii],
                        mod_stats[k+"_hist"][ii]))
            assert False


        run += 1
