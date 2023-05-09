import numpy as np
from . import dat


def read_rundict(dat_path, num_offset_bytes=4):
    rrr = {}
    with open(dat_path, "rb") as istream:
        with dat.RunReader(
            stream=istream, num_offset_bytes=num_offset_bytes
        ) as run:
            rrr["RUNH"] = run.runh
            rrr["events"] = []
            for event in run:
                evth, particle_block_reader = event
                eee = {
                    "EVTH": evth,
                    "particles": [],
                    "EVTE": None,
                }
                for particle_block in particle_block_reader:
                    for particle in particle_block:
                        eee["particles"].append(particle)
                eee["EVTE"] = particle_block_reader.evte
                rrr["events"].append(eee)
            rrr["RUNE"] = run.rune
        return rrr


def write_rundict(dat_path, rrr):
    with open(dat_path, "wb") as ostream:
        with dat.RunWriter(stream=ostream) as out:
            out.write_runh(rrr["RUNH"])
            for eee in rrr["events"]:
                out.write_evth(eee["EVTH"])
                for ppp in eee["particles"]:
                    out.write_particle(ppp)
                out.write_evte(eee["EVTE"])
            out.write_rune(rrr["RUNE"])


def assert_rundict_equal(rrr, bbb, ignore_rune=False, ignore_evte=False):
    np.testing.assert_array_equal(rrr["RUNH"], bbb["RUNH"])
    assert len(rrr["events"]) == len(bbb["events"])
    for i in range(len(rrr["events"])):
        eeer = rrr["events"][i]
        eeeb = bbb["events"][i]
        np.testing.assert_array_equal(eeer["EVTH"], eeeb["EVTH"])
        assert len(eeer["particles"]) == len(eeeb["particles"])
        for j in range(len(eeer["particles"])):
            np.testing.assert_array_equal(
                eeer["particles"][j], eeeb["particles"][j]
            )
        if not ignore_evte:
            np.testing.assert_array_equal(eeer["EVTE"], eeeb["EVTE"])
    if not ignore_rune:
        np.testing.assert_array_equal(rrr["RUNE"], bbb["RUNE"])
