import corsika_primary as cpw
import spherical_coordinates
import numpy as np


def test_drawing_cherenkov_photons():
    SPEED_OF_LIGHT_CM_PER_NS = 30.0

    prng = np.random.Generator(np.random.PCG64(9))

    for pointing in [[0, 0], [1, 1], [-1, 0.3]]:
        az, zd = pointing
        for instrument_pos in [[0, 0], [200, -100], [1337, -42]]:
            ins_x, ins_y = instrument_pos
            for dist in [1e2, 1e3, 1e4]:
                bunches = cpw.testing.draw_cherenkov_bunches_from_point_source(
                    instrument_sphere_x_cm=ins_x,
                    instrument_sphere_y_cm=ins_y,
                    instrument_sphere_radius_cm=100,
                    source_azimuth_rad=az,
                    source_zenith_rad=zd,
                    source_distance_to_instrument_cm=dist,
                    prng=prng,
                    size=1000,
                    speed_of_ligth_cm_per_ns=SPEED_OF_LIGHT_CM_PER_NS,
                )

                expected_source_incident = np.array(
                    spherical_coordinates.az_zd_to_cx_cy_cz(
                        azimuth_rad=az, zenith_rad=zd
                    )
                )
                expected_source_position = (
                    np.array([ins_x, ins_y, 0.0])
                    + dist * expected_source_incident
                )

                # reconstruct position of point source
                for i in range(len(bunches)):
                    x = bunches[i, cpw.I.BUNCH.X_CM]
                    y = bunches[i, cpw.I.BUNCH.Y_CM]
                    cx = bunches[i, cpw.I.BUNCH.CX_RAD]
                    cy = bunches[i, cpw.I.BUNCH.CY_RAD]

                    impact = np.array([x, y, 0])
                    incident = np.array(
                        [
                            cx,
                            cy,
                            spherical_coordinates.restore_cz(cx=cx, cy=cy),
                        ]
                    )

                    alpha_cm = (
                        bunches[i, cpw.I.BUNCH.TIME_NS]
                        * SPEED_OF_LIGHT_CM_PER_NS
                    )

                    reconstructed_source_position = (
                        impact + alpha_cm * incident
                    )

                    delta_cm = np.linalg.norm(
                        expected_source_position
                        - reconstructed_source_position
                    )
                    assert delta_cm < 1e-1

                assert (
                    np.abs(np.median(bunches[:, cpw.I.BUNCH.X_CM]) - ins_x)
                    < 10.0
                )
                assert (
                    np.abs(np.median(bunches[:, cpw.I.BUNCH.Y_CM]) - ins_y)
                    < 10.0
                )

                assert np.abs(
                    np.median(bunches[:, cpw.I.BUNCH.CX_RAD])
                    - expected_source_incident[0]
                ) < np.deg2rad(5.0)
                assert np.abs(
                    np.median(bunches[:, cpw.I.BUNCH.CY_RAD])
                    - expected_source_incident[1]
                ) < np.deg2rad(5.0)

                expected_time_ns = dist / SPEED_OF_LIGHT_CM_PER_NS
                assert (
                    np.abs(
                        np.median(bunches[:, cpw.I.BUNCH.TIME_NS])
                        - expected_time_ns
                    )
                    < 1.0
                )


def test_timing():
    SPEED_OF_LIGHT_CM_PER_NS = 30.0

    prng = np.random.Generator(np.random.PCG64(9))
    zeniths_rad = np.linspace(0.0, np.deg2rad(70), 10)
    dts_ns = []

    for zenith_rad in zeniths_rad:
        bunches = cpw.testing.draw_cherenkov_bunches_from_point_source(
            instrument_sphere_x_cm=0,
            instrument_sphere_y_cm=0,
            instrument_sphere_radius_cm=1e2 * 1e1,
            source_azimuth_rad=0,
            source_zenith_rad=zenith_rad,
            source_distance_to_instrument_cm=1e2 * 1e3,
            prng=prng,
            size=1000,
            speed_of_ligth_cm_per_ns=SPEED_OF_LIGHT_CM_PER_NS,
        )

        dt_ns = np.std(bunches[:, cpw.I.BUNCH.TIME_NS])
        dts_ns.append(dt_ns)

    assert np.all(
        np.gradient(dts_ns) > 0
    ), "expected time spread to rise with rising off axis."
