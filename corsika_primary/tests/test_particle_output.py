import pytest
import corsika_primary as cpw
import inspect
import numpy as np
import copy
import tempfile
import os

i8 = np.int64
f8 = np.float64


@pytest.fixture()
def corsika_primary_path(pytestconfig):
    return pytestconfig.getoption("corsika_primary_path")


@pytest.fixture()
def debug_dir(pytestconfig):
    return pytestconfig.getoption("debug_dir")


def test_particle_output(corsika_primary_path, debug_dir):
    tmp = cpw.testing.TmpDebugDir(
        debug_dir=debug_dir,
        suffix=inspect.getframeinfo(inspect.currentframe()).function,
    )

    path = os.path.join(tmp.name, "cer.tar")
    particle_output_path = path + ".dat"

    steering = copy.deepcopy(cpw.steering.EXAMPLE)

    steering["run"]["energy_range"] = {
        "start_GeV": f8(100.0),
        "stop_GeV": f8(200.0),
    }
    steering["primaries"] = [
        {
            "particle_id": f8(14),
            "energy_GeV": f8(100.0),
            "zenith_rad": f8(0.0),
            "azimuth_rad": f8(0.0),
            "depth_g_per_cm2": f8(0.0),
        },
        {
            "particle_id": f8(402),
            "energy_GeV": f8(180.0),
            "zenith_rad": f8(0.0),
            "azimuth_rad": f8(0.0),
            "depth_g_per_cm2": f8(0.0),
        },
    ]

    if not os.path.exists(particle_output_path):
        cpw.corsika_primary(
            corsika_path=corsika_primary_path,
            steering_dict=steering,
            stdout_path=path + ".o",
            stderr_path=path + ".e",
            output_path=path,
            particle_output_path=particle_output_path,
        )

    with cpw.particles.BlockReader(path=particle_output_path) as br:
        _ = br.__repr__()
        for block in br:
            block_marker = block[0]
            if block_marker.tobytes() in [b"RUNH", b"EVTH", b"EVTE", b"RUNE"]:
                continue

            if block_marker == np.float32(0.0):
                continue

            particle_id = cpw.particles.decode_particle_id(block_marker)
            if 1 <= particle_id <= 195:
                continue

            assert False, "Bad block_marker"

    rrr = {}
    with cpw.particles.RunReader(path=particle_output_path) as run:
        _ = run.__repr__()

        assert run.runh[0].tobytes() == b"RUNH"
        rrr["RUNH"] = run.runh
        rrr["events"] = []

        for event in run:
            evth, particle_block_reader = event

            eee = {
                "EVTH": evth,
                "particles": [],
                "EVTE": None,
            }

            assert evth[0].tobytes() == b"EVTH"

            _ = particle_block_reader.__repr__()

            for particle_block in particle_block_reader:
                for particle in particle_block:
                    particle_id = cpw.particles.decode_particle_id(
                        particle[cpw.I.PARTICLE.CODE]
                    )

                    assert 1 <= particle_id <= 195

                    E = np.linalg.norm(
                        [
                            particle[cpw.I.PARTICLE.PX],
                            particle[cpw.I.PARTICLE.PY],
                            particle[cpw.I.PARTICLE.PZ],
                        ]
                    )

                    xx = particle[cpw.I.PARTICLE.X] * 1e-2
                    yy = particle[cpw.I.PARTICLE.Y] * 1e-2

                    # print("ID", particle_id, ", E: {:.1f}GeV, ".format(E)," POS: ({:.1f},{:.1f})m".format(xx, yy))

                    eee["particles"].append(particle)

            assert particle_block_reader.evte[0].tobytes() == b"EVTE"
            eee["EVTE"] = particle_block_reader.evte
            rrr["events"].append(eee)

        assert run.rune[0].tobytes() == b"RUNE"
        rrr["RUNE"] = run.rune

        assert run.block_reader.file.closed == False

    assert run.block_reader.file.closed == True

    cpw.particles.write_rundict(path=particle_output_path + ".back", rrr=rrr)
    bbb = cpw.particles.read_rundict(path=particle_output_path + ".back")

    # compare rrr and bbb
    # ===================

    cpw.particles.assert_rundict_equal(rrr=rrr, bbb=bbb)

    tmp.cleanup_when_no_debug()
