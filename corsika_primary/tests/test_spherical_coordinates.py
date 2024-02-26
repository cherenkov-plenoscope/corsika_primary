import pytest
import os
import tempfile
import corsika_primary as cpw
import inspect
import numpy as np
import spherical_coordinates


@pytest.fixture()
def debug_dir(pytestconfig):
    return pytestconfig.getoption("debug_dir")


@pytest.fixture()
def corsika_primary_path(pytestconfig):
    return pytestconfig.getoption("corsika_primary_path")


i4 = np.int32
i8 = np.int64
f8 = np.float64


def test_spherical_coordinates_in_corsika(debug_dir, corsika_primary_path):
    tmp = cpw.testing.TmpDebugDir(
        debug_dir=debug_dir,
        suffix=inspect.getframeinfo(inspect.currentframe()).function,
    )

    num_shower = 1000
    observation_level_asl_m = 5000
    earth_magnetic_field_x_muT = 20.815
    earth_magnetic_field_z_muT = -11.366
    atmosphere_id = 7
    seed = 42
    particle_id = 1  # gamma
    energy = 0.25

    prng = np.random.Generator(np.random.PCG64(seed))

    steering = {
        "run": {
            "run_id": i8(seed),
            "event_id_of_first_event": i8(1),
            "observation_level_asl_m": f8(observation_level_asl_m),
            "earth_magnetic_field_x_muT": f8(earth_magnetic_field_x_muT),
            "earth_magnetic_field_z_muT": f8(earth_magnetic_field_z_muT),
            "atmosphere_id": i8(atmosphere_id),
            "energy_range": {"start_GeV": f8(0.2), "stop_GeV": f8(0.3)},
            "random_seed": cpw.random.seed.make_simple_seed(seed=seed),
        },
        "primaries": [],
    }

    for idx in range(num_shower):
        az, zd = cpw.random.distributions.draw_azimuth_zenith_in_viewcone(
            prng=prng,
            azimuth_rad=0.0,
            zenith_rad=0.0,
            min_scatter_opening_angle_rad=0.0,
            max_scatter_opening_angle_rad=np.deg2rad(60),
        )
        prm = {
            "particle_id": f8(particle_id),
            "energy_GeV": f8(energy),
            "zenith_rad": f8(zd),
            "azimuth_rad": f8(az),
            "depth_g_per_cm2": f8(0.0),
        }
        steering["primaries"].append(prm)

    events_cer_ux = []
    events_cer_vy = []
    with cpw.CorsikaPrimary(
        corsika_path=corsika_primary_path,
        steering_dict=steering,
        stdout_path=os.path.join(tmp.name, "run.o"),
        stderr_path=os.path.join(tmp.name, "run.e"),
        particle_output_path=os.path.join(tmp.name, "run.par.dat"),
    ) as run:
        for event in run:
            evth, cer_reader = event

            cer = np.concatenate([block for block in cer_reader])
            if cer.shape[0] >= 1000:
                events_cer_ux.append(np.median(cer[:, cpw.I.BUNCH.UX_1]))
                events_cer_vy.append(np.median(cer[:, cpw.I.BUNCH.VY_1]))
            else:
                events_cer_ux.append(float("nan"))
                events_cer_vy.append(float("nan"))

    # test
    # ----
    for idx in range(num_shower):
        par_az = steering["primaries"][idx]["azimuth_rad"]
        par_zd = steering["primaries"][idx]["zenith_rad"]

        cer_ux = events_cer_ux[idx]
        cer_vy = events_cer_vy[idx]

        if not np.isnan(cer_ux):
            par_cxcycz = spherical_coordinates.az_zd_to_cx_cy_cz(
                azimuth_rad=par_az,
                zenith_rad=par_zd,
            )

            cer_cx = spherical_coordinates.corsika.ux_to_cx(cer_ux)
            cer_cy = spherical_coordinates.corsika.vy_to_cy(cer_vy)
            cer_cz = spherical_coordinates.restore_cz(cx=cer_cx, cy=cer_cy)

            delta_rad = spherical_coordinates.angle_between_cx_cy_cz(
                cx1=par_cxcycz[0],
                cy1=par_cxcycz[1],
                cz1=par_cxcycz[2],
                cx2=cer_cx,
                cy2=cer_cy,
                cz2=cer_cz,
            )
            print(np.rad2deg(par_zd), np.rad2deg(delta_rad), "deg")

    tmp.cleanup_when_no_debug()
