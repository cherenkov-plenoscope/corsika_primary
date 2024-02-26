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
    energy = 0.5

    prng = np.random.Generator(np.random.PCG64(seed))

    steering = {
        "run": {
            "run_id": i8(seed),
            "event_id_of_first_event": i8(1),
            "observation_level_asl_m": f8(observation_level_asl_m),
            "earth_magnetic_field_x_muT": f8(earth_magnetic_field_x_muT),
            "earth_magnetic_field_z_muT": f8(earth_magnetic_field_z_muT),
            "atmosphere_id": i8(atmosphere_id),
            "energy_range": {"start_GeV": f8(0.4), "stop_GeV": f8(0.6)},
            "random_seed": cpw.random.seed.make_simple_seed(seed=seed),
        },
        "primaries": [],
    }

    events = []
    for idx in range(num_shower):
        event = {}
        (
            event["prm_azimuth_rad"],
            event["prm_zenith_rad"],
        ) = cpw.random.distributions.draw_azimuth_zenith_in_viewcone(
            prng=prng,
            azimuth_rad=0.0,
            zenith_rad=0.0,
            min_scatter_opening_angle_rad=0.0,
            max_scatter_opening_angle_rad=np.deg2rad(60),
        )
        event["prm_phi_rad"] = spherical_coordinates.corsika.az_to_phi(
            event["prm_azimuth_rad"]
        )
        event["prm_theta_rad"] = spherical_coordinates.corsika.zd_to_theta(
            event["prm_zenith_rad"]
        )

        prm = {
            "particle_id": f8(particle_id),
            "energy_GeV": f8(energy),
            "theta_rad": f8(event["prm_theta_rad"]),
            "phi_rad": f8(event["prm_phi_rad"]),
            "depth_g_per_cm2": f8(0.0),
        }
        steering["primaries"].append(prm)
        events.append(event)

    with cpw.CorsikaPrimary(
        corsika_path=corsika_primary_path,
        steering_dict=steering,
        stdout_path=os.path.join(tmp.name, "run.o"),
        stderr_path=os.path.join(tmp.name, "run.e"),
        particle_output_path=os.path.join(tmp.name, "run.par.dat"),
    ) as run:
        for i, event in enumerate(run):
            evth, cer_reader = event
            cer = np.concatenate([block for block in cer_reader])

            if cer.shape[0] >= 1e4:
                events[i]["cer_ux"] = np.median(cer[:, cpw.I.BUNCH.UX_1])
                events[i]["cer_vy"] = np.median(cer[:, cpw.I.BUNCH.VY_1])
            else:
                events[i]["cer_ux"] = float("nan")
                events[i]["cer_vy"] = float("nan")

    # test
    # ----
    for i in range(num_shower):
        event = events[i]
        if not np.isnan(event["cer_ux"]):
            prm_cxcycz = spherical_coordinates.az_zd_to_cx_cy_cz(
                azimuth_rad=event["prm_azimuth_rad"],
                zenith_rad=event["prm_zenith_rad"],
            )

            cer_cx = spherical_coordinates.corsika.ux_to_cx(event["cer_ux"])
            cer_cy = spherical_coordinates.corsika.vy_to_cy(event["cer_vy"])
            cer_cz = spherical_coordinates.restore_cz(cx=cer_cx, cy=cer_cy)

            delta_rad = spherical_coordinates.angle_between_cx_cy_cz(
                cx1=prm_cxcycz[0],
                cy1=prm_cxcycz[1],
                cz1=prm_cxcycz[2],
                cx2=cer_cx,
                cy2=cer_cy,
                cz2=cer_cz,
            )

            event["prm_cer_delta_rad"] = delta_rad

    num_bright_enough = 0
    num_delta_le_15deg = 0
    num_delta_le_10deg = 0
    num_delta_le_5deg = 0
    for i in range(num_shower):
        event = events[i]
        if "prm_cer_delta_rad" in event:
            num_bright_enough += 1
            if np.rad2deg(event["prm_cer_delta_rad"]) <= 15:
                num_delta_le_15deg += 1
            if np.rad2deg(event["prm_cer_delta_rad"]) <= 10:
                num_delta_le_10deg += 1
            if np.rad2deg(event["prm_cer_delta_rad"]) <= 5:
                num_delta_le_5deg += 1

    if True:
        print(
            "num_shower:",
            num_shower,
            ", " "num_bright_enough:",
            num_bright_enough,
            ", " "num_delta_le_15deg:",
            num_delta_le_15deg,
            ", " "num_delta_le_10deg:",
            num_delta_le_10deg,
            ", " "num_delta_le_5deg:",
            num_delta_le_5deg,
        )

    assert num_bright_enough >= 0.5 * num_shower
    assert num_delta_le_15deg / num_bright_enough > 0.97
    assert num_delta_le_10deg / num_bright_enough > 0.92
    assert num_delta_le_5deg / num_bright_enough > 0.75

    tmp.cleanup_when_no_debug()
