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

    steering = cpw.testing.make_example_steering_for_particle_output()

    vvv_path = os.path.join(tmp.name, "VVV")
    vvv_cer_path = vvv_path + ".cer.tar"
    vvv_par_path = vvv_path + ".par.dat"

    if not os.path.exists(vvv_par_path):
        cpw.corsika_primary(
            corsika_path=corsika_primary_path,
            steering_dict=steering,
            stdout_path=vvv_path + ".o",
            stderr_path=vvv_path + ".e",
            cherenkov_output_path=vvv_cer_path,
            particle_output_path=vvv_par_path,
        )

    with open(vvv_par_path, "rb") as vvvstream:
        with cpw.particles.dat.BlockReader(stream=vvvstream) as br:
            _ = br.__repr__()
            for block in br:
                block_marker = block[0]
                if block_marker.tobytes() in [
                    b"RUNH",
                    b"EVTH",
                    b"EVTE",
                    b"RUNE",
                ]:
                    continue

                if block_marker == np.float32(0.0):
                    continue

                particle_id = cpw.particles.decode_particle_id(block_marker)
                if 1 <= particle_id <= 195:
                    continue

                assert False, "Bad block_marker"

    rrr = {}
    with open(vvv_par_path, "rb") as vvvstream:
        with cpw.particles.dat.RunReader(stream=vvvstream) as run:
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

    cpw.particles.rundict.write_rundict(
        dat_path=vvv_par_path + ".back", rrr=rrr
    )
    bbb = cpw.particles.rundict.read_rundict(dat_path=vvv_par_path + ".back")

    # compare rrr and bbb
    # ===================
    cpw.particles.rundict.assert_rundict_equal(rrr=rrr, bbb=bbb)

    tmp.cleanup_when_no_debug()
