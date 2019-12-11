import pytest
import os
import tempfile
import corsika_primary_wrapper as cpw
import corsika_wrapper as cw
import simpleio
import numpy as np
import subprocess
import pandas as pd
import struct


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

"""

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
"""

def bit_string(flt):
    return bin(struct.unpack('!i',struct.pack('!f', flt))[0])


KEYS = ['x', 'y', 'cx', 'cy', 'time', 'zem', 'bsize', 'wvl']
SPPED_OF_LIGHT = 299792458

def _init_statistics():
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

    num_shower = 7

    chi_g_per_cm2 = 0.0
    obs_level = 2.3e3
    earth_magnetic_field_x_muT = 12.5
    earth_magnetic_field_z_muT = -25.9
    atmosphere_id = 10
    zenith_deg = 0.
    azimuth_deg = 0.
    telescope_sphere_radius = 1e4

    cfg = {
        "gamma": {"id": 1, "energy": 1.337},
        "electron": {"id": 3, "energy": 1.337},
        "proton": {"id": 14, "energy": 7.0},
    }

    run = 0
    for particle in cfg:
        with tempfile.TemporaryDirectory(prefix="test_primary_") as tmp_dir:
            tmp_dir = "/home/sebastian/Desktop/test_primary_{:d}".format(run)
            os.makedirs(tmp_dir, exist_ok=True)



            # RUN ORIGINAL CORSIKA
            # --------------------
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


            ori_run_eventio_path = os.path.join(
                tmp_dir,
                "original_run_{:d}.eventio".format(run))
            ori_run_path = os.path.join(
                tmp_dir,
                "original_run_{:d}.simpleio".format(run))
            if not os.path.exists(ori_run_path):
                ori_card_path = os.path.join(
                    tmp_dir,
                    "original_steering_card_{:d}.txt".format(run))
                with open(ori_card_path, "wt") as f:
                    f.write(ori_steering_card)
                cw.corsika(
                    steering_card=cw.read_steering_card(ori_card_path),
                    output_path=ori_run_eventio_path,
                    save_stdout=True,
                    corsika_path=corsika_path)
                subprocess.call([
                    merlict_eventio_converter,
                    "-i", ori_run_eventio_path,
                    "-o", ori_run_path])

            with open(ori_run_eventio_path+".stdout", "rt") as f:
                ori_stdout = f.read()
            ori_events_seeds = cpw._parse_random_seeds_from_corsika_stdout(
                stdout=ori_stdout)

            print(ori_events_seeds)

            # RUN MODIFIED CORSIKA
            # --------------------
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
                    "random_seed": ori_events_seeds[idx_primary],
                }
                mod_steering_dict["primaries"].append(prm)

            mod_run_path = os.path.join(
                tmp_dir,
                "modified_run_{:d}.tar".format(run))
            if not os.path.exists(mod_run_path):
                cpw.corsika_primary(
                    corsika_path=corsika_primary_path,
                    steering_dict=mod_steering_dict,
                    output_path=mod_run_path)

            # READ ORIGINAL AND MODIFIED RUNS
            # -------------------------------
            mod_run = cpw.Tario(mod_run_path)
            ori_run = simpleio.SimpleIoRun(ori_run_path)

            # ori_stats = _init_statistics()
            # mod_stats = _init_statistics()
            for evt_idx in range(num_shower):
                mod_evth, _mod_bunches = next(mod_run)
                mod_bunches = _tario_bunches_to_array(_mod_bunches)
                _ori_event = ori_run[evt_idx]
                ori_evth = _ori_event.header.raw
                ori_bunches = _simpleio_bunches_to_array(
                    _ori_event.cherenkov_photon_bunches)
                # ori_stats = _append_bunch_statistics(ori_stats, ori_bunches)
                # mod_stats = _append_bunch_statistics(mod_stats, mod_bunches)

                with open(os.path.join(tmp_dir, "evth_compare.md"), "at") as fout:
                    md = "---------------{: 3d}--------------\n".format(
                        evt_idx+1)
                    for ll in range(ori_evth.shape[0]):
                        ll_diff = mod_evth[ll] - ori_evth[ll]
                        if np.abs(ll_diff) > 0.0:
                            md += "{: 3d} {:3.3f} {:3.3f} {:3.3f}\n".format(
                                ll+1, mod_evth[ll], ori_evth[ll],
                                mod_evth[ll] - ori_evth[ll])
                        else:
                            md += "{: 3d}\n".format(
                                ll+1, mod_evth[ll])
                    fout.write(md)

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

                print(run, ori_bunches.shape[0], mod_bunches.shape[0])

                if zenith_deg == 0. and azimuth_deg == 0.:
                    # When angles are different from zero, numeric precision
                    # will cause slightly differrent start values for primary.
                    assert ori_bunches.shape[0] == mod_bunches.shape[0]
                else:
                    assert (
                        np.abs(ori_bunches.shape[0] - mod_bunches.shape[0]) <
                        1000)

                if ori_bunches.shape[0] == mod_bunches.shape[0]:
                    np.testing.assert_array_almost_equal(
                        x=mod_bunches[:, ICX],
                        y=ori_bunches[:, ICX],
                        decimal=5)
                    np.testing.assert_array_almost_equal(
                        x=mod_bunches[:, ICY],
                        y=ori_bunches[:, ICY],
                        decimal=5)

                    np.testing.assert_array_almost_equal(
                        x=mod_bunches[:, IZEM],
                        y=ori_bunches[:, IZEM],
                        decimal=1)
                    np.testing.assert_array_almost_equal(
                        x=mod_bunches[:, IBSIZE],
                        y=ori_bunches[:, IBSIZE],
                        decimal=6)
                    np.testing.assert_array_almost_equal(
                        x=mod_bunches[:, IWVL],
                        y=ori_bunches[:, IWVL],
                        decimal=9)

                    # Correct for detector-sphere in iact.c
                    # See function: photon_hit()
                    # -------------------------------------
                    DET_ZO = telescope_sphere_radius
                    DET_XO = 0.
                    DET_YO = 0.
                    cx2_cy2 = mod_bunches[:, ICX]**2 + mod_bunches[:, ICY]**2
                    mod_sx = mod_bunches[:, ICX]/np.sqrt(1.-cx2_cy2)
                    mod_sy = mod_bunches[:, ICY]/np.sqrt(1.-cx2_cy2)

                    mod_x = mod_bunches[:, IX] - mod_sx*DET_ZO - DET_XO
                    mod_y = mod_bunches[:, IY] - mod_sy*DET_ZO - DET_YO

                    if particle != "electron" and particle != "proton":
                        # Charged cosimc-rays such as electron and proton
                        # have corrections implemented in iact.c for
                        # deflections in earth's magnetic field.
                        np.testing.assert_array_almost_equal(
                            x=mod_x,
                            y=ori_bunches[:, IX],
                            decimal=2)
                        np.testing.assert_array_almost_equal(
                            x=mod_y,
                            y=ori_bunches[:, IY],
                            decimal=2)

                        HEIGHT_AT_ZERO_GRAMMAGE = 112.8e3
                        assert (
                            cpw._evth_z_coordinate_of_first_interaction_cm(
                                mod_evth) < 0.)
                        assert (
                            cpw._evth_z_coordinate_of_first_interaction_cm(
                                ori_evth) < 0.)

                        mod_time_sphere_z = (
                            DET_ZO*np.sqrt(1.+mod_sx**2+mod_sy**2)/
                            SPPED_OF_LIGHT)

                        mod_zenith_rad = cpw._evth_zenith_rad(mod_evth)

                        mod_toffset = (HEIGHT_AT_ZERO_GRAMMAGE + obs_level
                            )/np.cos(mod_zenith_rad)/SPPED_OF_LIGHT

                        #print("zenith_rad", mod_zenith_rad)
                        mod_ctime = mod_bunches[:, ITIME] - mod_time_sphere_z
                        mod_ctime = mod_ctime - mod_toffset

                        #print("sx", mod_sx[0:4])
                        #print("sy", mod_sy[0:4])
                        #print("toffset ns", mod_toffset*1e9)
                        #print("time_sphere_z ns", mod_time_sphere_z[0:4]*1e9)
                        #print("ori ns", 1e9*ori_bunches[0:4, ITIME])
                        #print("mod ns", 1e9*mod_bunches[0:4, ITIME])
                        #print("mod_ctime ns", 1e9*mod_ctime[0:4])

                        np.testing.assert_array_almost_equal(
                            x=mod_ctime,
                            y=ori_bunches[:, ITIME],
                            decimal=6)
        run += 1
