import pytest
import os
import tempfile
import corsika_primary_wrapper as cpw
from corsika_primary_wrapper import testing as cpw_testing
import corsika_wrapper as cw
import simpleio
import numpy as np
import subprocess
import pandas as pd
import struct

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
def merlict_eventio_converter(pytestconfig):
    return pytestconfig.getoption("merlict_eventio_converter")


@pytest.fixture()
def non_temporary_path(pytestconfig):
    return pytestconfig.getoption("non_temporary_path")


SPPED_OF_LIGHT_M_PER_S = 299792458


def equal(a, b, absolute_margin=1e-6):
    return np.abs(a - b) < absolute_margin


def evth_is_equal_enough(ori_evth, mod_evth):
    I_ENERGY_LOWER_LIMIT = 59
    I_ENERGY_UPPER_LIMIT = 60
    assert ori_evth.shape[0] == mod_evth.shape[0]
    equal = True
    for ii in range(ori_evth.shape[0]):
        if ii == (I_ENERGY_LOWER_LIMIT - 1):
            # Our CORSIKA-primary mod is told to only accept energies within
            # upper and lower limits. Therefore, a small overhead is added when
            # declaring the energy-limits to CORSIKA in the beginning of a run.
            d = np.abs(
                ori_evth[ii] * (1.0 - cpw.steering.ENERGY_LIMIT_OVERHEAD)
                - mod_evth[ii]
            )
            if d > 1e-6:
                equal = False

        elif ii == (I_ENERGY_UPPER_LIMIT - 1):
            d = np.abs(
                ori_evth[ii] * (1.0 + cpw.steering.ENERGY_LIMIT_OVERHEAD)
                - mod_evth[ii]
            )
            if d > 1e-6:
                equal = False

        elif ii == (77 - 1):
            # We ignore field 77. (fortran77 idx starts at 1)
            # Here iact.c sets a flag in case of VOLUMEDET option.
            # Its only relevant for the geometry of the scattering,
            # what is obsolete now.
            pass
        else:
            if ori_evth[ii] != mod_evth[ii]:
                equal = False
    return equal


def test_original_vs_moddified(
    corsika_primary_path,
    corsika_path,
    merlict_eventio_converter,
    non_temporary_path,
):
    """
    For gammas and electrons, check the Cherenkov-light-field
    of original and moddified CORAIKA to be euqal.
    For protons check at least its similar.
    Protons scatter so much that thir Cherenkov-light-field can not be fully
    contained in the original output.
    """
    assert os.path.exists(corsika_primary_path)
    assert os.path.exists(corsika_path)
    assert os.path.exists(merlict_eventio_converter)

    num_shower = 7

    chi_g_per_cm2 = 0.0
    obs_level_m = 2.3e3
    earth_magnetic_field_x_muT = 12.5
    earth_magnetic_field_z_muT = -25.9
    atmosphere_id = 10
    zenith_deg = 0.0
    azimuth_deg = 0.0
    telescope_sphere_radius_m = 1e4

    cfg = {
        "gamma": {"id": 1, "energy": 1.337},
        "electron": {"id": 3, "energy": 1.337},
        "proton": {"id": 14, "energy": 7.0},
    }

    run = 0
    tmp_prefix = "test_original_vs_modified_"
    for particle in cfg:
        with tempfile.TemporaryDirectory(prefix=tmp_prefix) as tmp_dir:
            if non_temporary_path != "":
                tmp_dir = os.path.join(
                    non_temporary_path, tmp_prefix + "_{:d}".format(run)
                )
                os.makedirs(tmp_dir, exist_ok=True)

            # RUN ORIGINAL CORSIKA
            # --------------------
            ori_steering_card = "\n".join(
                [
                    "RUNNR 1",
                    "EVTNR 1",
                    "NSHOW {:d}".format(num_shower),
                    "PRMPAR {:d}".format(cfg[particle]["id"]),
                    "ESLOPE 0",
                    "ERANGE {:f} {:f}".format(
                        cfg[particle]["energy"], cfg[particle]["energy"]
                    ),
                    "THETAP {:f} {:f}".format(zenith_deg, zenith_deg),
                    "PHIP {:f} {:f}".format(azimuth_deg, azimuth_deg),
                    "VIEWCONE 0 0",
                    "SEED 1 0 0",
                    "SEED 2 0 0",
                    "SEED 3 0 0",
                    "SEED 4 0 0",
                    "OBSLEV {:f}".format(1e2 * obs_level_m),
                    "FIXCHI {:f}".format(chi_g_per_cm2),
                    "MAGNET {Bx:3.3e} {Bz:3.3e}".format(
                        Bx=earth_magnetic_field_x_muT,
                        Bz=earth_magnetic_field_z_muT,
                    ),
                    "ELMFLG T T",
                    "MAXPRT 1",
                    "PAROUT F F",
                    "TELESCOPE 0 0 0 {:f}".format(
                        1e2 * telescope_sphere_radius_m
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

            ori_run_eventio_path = os.path.join(
                tmp_dir, "original_run_{:d}.eventio".format(run)
            )
            ori_run_path = os.path.join(
                tmp_dir, "original_run_{:d}.simpleio".format(run)
            )
            if not os.path.exists(ori_run_path):
                ori_card_path = os.path.join(
                    tmp_dir, "original_steering_card_{:d}.txt".format(run)
                )
                with open(ori_card_path, "wt") as f:
                    f.write(ori_steering_card)
                cw.corsika(
                    steering_card=cw.read_steering_card(ori_card_path),
                    output_path=ori_run_eventio_path,
                    save_stdout=True,
                    corsika_path=corsika_path,
                )
                subprocess.call(
                    [
                        merlict_eventio_converter,
                        "-i",
                        ori_run_eventio_path,
                        "-o",
                        ori_run_path,
                    ]
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
                    "observation_level_asl_m": f8(obs_level_m),
                    "earth_magnetic_field_x_muT": f8(
                        earth_magnetic_field_x_muT
                    ),
                    "earth_magnetic_field_z_muT": f8(
                        earth_magnetic_field_z_muT
                    ),
                    "atmosphere_id": i8(atmosphere_id),
                    "energy_range": {
                        "start_GeV": f8(
                            cfg[particle]["energy"]
                            * (1 - cpw.steering.ENERGY_LIMIT_OVERHEAD)
                        ),
                        "stop_GeV": f8(
                            cfg[particle]["energy"]
                            * (1 + cpw.steering.ENERGY_LIMIT_OVERHEAD)
                        ),
                    },
                },
                "primaries": [],
            }

            for idx_primary in range(num_shower):
                prm = {
                    "particle_id": f8(cfg[particle]["id"]),
                    "energy_GeV": f8(cfg[particle]["energy"]),
                    "zenith_rad": f8(np.deg2rad(zenith_deg)),
                    "azimuth_rad": f8(np.deg2rad(azimuth_deg)),
                    "depth_g_per_cm2": f8(chi_g_per_cm2),
                    "random_seed": ori_events_seeds[idx_primary],
                }
                mod_steering_dict["primaries"].append(prm)

            mod_run_path = os.path.join(
                tmp_dir, "modified_run_{:d}.tar".format(run)
            )
            if not os.path.exists(mod_run_path):
                cpw.corsika_primary(
                    corsika_path=corsika_primary_path,
                    steering_dict=mod_steering_dict,
                    output_path=mod_run_path,
                )

            # READ ORIGINAL AND MODIFIED RUNS
            # -------------------------------
            mod_run = cpw.Tario(mod_run_path)
            ori_run = simpleio.SimpleIoRun(ori_run_path)

            for evt_idx in range(num_shower):
                mod_evth, _mod_bunches = next(mod_run)
                mod_bunches = cpw_testing.tario_bunches_to_array(_mod_bunches)
                _ori_event = ori_run[evt_idx]
                ori_evth = _ori_event.header.raw
                ori_bunches = cpw_testing.simpleio_bunches_to_array(
                    _ori_event.cherenkov_photon_bunches
                )

                evth_compare_path = os.path.join(tmp_dir, "evth_compare.md")
                with open(evth_compare_path, "at") as fout:
                    md = "---------------{: 3d}--------------\n".format(
                        evt_idx + 1
                    )
                    for ll in range(ori_evth.shape[0]):
                        ll_diff = mod_evth[ll] - ori_evth[ll]
                        if np.abs(ll_diff) > 0.0:
                            md += "{: 3d} {:3.3f} {:3.3f} {:3.3f}\n".format(
                                ll + 1,
                                mod_evth[ll],
                                ori_evth[ll],
                                mod_evth[ll] - ori_evth[ll],
                            )
                        else:
                            md += "{: 3d}\n".format(ll + 1, mod_evth[ll])
                    fout.write(md)

                assert evth_is_equal_enough(
                    ori_evth=ori_evth, mod_evth=mod_evth
                )

                if particle == "proton":
                    assert ori_num_bunches[evt_idx] == mod_bunches.shape[0]
                else:

                    print(run, ori_bunches.shape[0], mod_bunches.shape[0])

                    if zenith_deg == 0.0 and azimuth_deg == 0.0:
                        # When angles are different from zero, numeric
                        # precision will cause slightly differrent start
                        # values for primary.
                        assert ori_bunches.shape[0] == mod_bunches.shape[0]
                    else:
                        assert (
                            np.abs(ori_bunches.shape[0] - mod_bunches.shape[0])
                            < 1000
                        )

                    if ori_bunches.shape[0] == mod_bunches.shape[0]:
                        np.testing.assert_array_almost_equal(
                            x=mod_bunches[:, cpw.ICX],
                            y=ori_bunches[:, cpw.ICX],
                            decimal=5,
                        )
                        np.testing.assert_array_almost_equal(
                            x=mod_bunches[:, cpw.ICY],
                            y=ori_bunches[:, cpw.ICY],
                            decimal=5,
                        )

                        np.testing.assert_array_almost_equal(
                            x=mod_bunches[:, cpw.IZEM],
                            y=ori_bunches[:, cpw.IZEM],
                            decimal=1,
                        )
                        np.testing.assert_array_almost_equal(
                            x=mod_bunches[:, cpw.IBSIZE],
                            y=ori_bunches[:, cpw.IBSIZE],
                            decimal=6,
                        )
                        np.testing.assert_array_almost_equal(
                            x=mod_bunches[:, cpw.IWVL],
                            y=ori_bunches[:, cpw.IWVL],
                            decimal=9,
                        )

                        # Correct for detector-sphere in iact.c
                        # See function: photon_hit()
                        # -------------------------------------
                        """
                        ^
                        |                         _______
                        |                     ___/       |___
                        |                    /          /    |_
                        |                  /    radius /       |
                        |                 |           /         |
                        z = DET_Z - - - - | - - - - -X- - - - - |- - - -
                        |                 |                     |
                        |                  |_                 _/
                        |                    |___         ___/
                        z = obs. lvl.  . . . . . |_______| . . . . . . .
                        |
                        |                            |
                        |                      DET_X / DET_Y
                        z = 0m a.s.l.

                        The mod_bunches have their supports x,y wrt. the
                        observation-level.
                        The ori_bunches have their supports x,y wrt. the
                        plane centered in the detector-sphere.
                        """
                        DET_XO = 0.0
                        DET_YO = 0.0
                        DET_ZO = telescope_sphere_radius_m
                        cx2_cy2 = (
                            mod_bunches[:, cpw.ICX] ** 2
                            + mod_bunches[:, cpw.ICY] ** 2
                        )
                        mod_sx = mod_bunches[:, cpw.ICX] / np.sqrt(
                            1.0 - cx2_cy2
                        )
                        mod_sy = mod_bunches[:, cpw.ICY] / np.sqrt(
                            1.0 - cx2_cy2
                        )

                        mod_x_wrt_detector_sphere = (
                            mod_bunches[:, cpw.IX] - mod_sx * DET_ZO - DET_XO
                        )
                        mod_y_wrt_detector_sphere = (
                            mod_bunches[:, cpw.IY] - mod_sy * DET_ZO - DET_YO
                        )

                        # ctime
                        # -----
                        HEIGHT_AT_ZERO_GRAMMAGE_M = 112.8e3
                        mod_time_sphere_z = (
                            DET_ZO
                            * np.sqrt(1.0 + mod_sx ** 2 + mod_sy ** 2)
                            / SPPED_OF_LIGHT_M_PER_S
                        )

                        mod_zenith_rad = mod_evth[cpw.I_EVTH_ZENITH_RAD]

                        mod_toffset = (
                            (HEIGHT_AT_ZERO_GRAMMAGE_M + obs_level_m)
                            / np.cos(mod_zenith_rad)
                            / SPPED_OF_LIGHT_M_PER_S
                        )

                        mod_ctime_wrt_detector_sphere = (
                            mod_bunches[:, cpw.ITIME] - mod_time_sphere_z
                        )
                        mod_ctime_wrt_detector_sphere -= mod_toffset

                        np.testing.assert_array_almost_equal(
                            x=mod_ctime_wrt_detector_sphere,
                            y=ori_bunches[:, cpw.ITIME],
                            decimal=6,
                        )

                        # x-y-supports
                        # ------------
                        if particle == "gamma":
                            # Charged cosimc-rays such as electron and proton
                            # have corrections implemented in iact.c for
                            # deflections in earth's magnetic field.
                            np.testing.assert_array_almost_equal(
                                x=mod_x_wrt_detector_sphere,
                                y=ori_bunches[:, cpw.IX],
                                decimal=2,
                            )
                            np.testing.assert_array_almost_equal(
                                x=mod_y_wrt_detector_sphere,
                                y=ori_bunches[:, cpw.IY],
                                decimal=2,
                            )

                            assert (
                                mod_evth[cpw.I_EVTH_Z_FIRST_INTERACTION_CM]
                                < 0.0
                            )
                            assert (
                                ori_evth[cpw.I_EVTH_Z_FIRST_INTERACTION_CM]
                                < 0.0
                            )
                        elif particle == "electron":
                            # subtract the xy-offset which was added in iact.c
                            # to correct for magnetig defelction
                            mod_x_wrt_mean = (
                                mod_x_wrt_detector_sphere
                                - np.mean(mod_x_wrt_detector_sphere)
                            )
                            mod_y_wrt_mean = (
                                mod_y_wrt_detector_sphere
                                - np.mean(mod_y_wrt_detector_sphere)
                            )

                            _ori_x = ori_bunches[:, cpw.IX]
                            _ori_y = ori_bunches[:, cpw.IY]
                            ori_x_wrt_mean = _ori_x - np.mean(_ori_x)
                            ori_y_wrt_mean = _ori_y - np.mean(_ori_y)

                            np.testing.assert_array_almost_equal(
                                x=mod_x_wrt_mean, y=ori_x_wrt_mean, decimal=2
                            )
                            np.testing.assert_array_almost_equal(
                                x=mod_y_wrt_mean, y=ori_y_wrt_mean, decimal=2
                            )
        run += 1
