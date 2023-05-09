import numpy as np
from . import dat
from . import tape
from . import rundict
from .. import event_tape


def ParticleEventTapeWriter(path, buffer_capacity=1000 * 1000):
    """
    Write a ParticleEventTape. Add RUNH, EVTH, and particles.

    path : str
        Path to event-tape file.
    buffer_capacity : int
        Buffer-size in num. particles.
    """
    return event_tape.TapeWriter(
        path=path,
        payload_shape_1=7,
        payload_block_suffix=PARTICLE_SUFFIX,
        buffer_capacity=buffer_capacity,
    )


def ParticleEventTapeReader(path):
    return event_tape.EventTapeReader(
        path=path,
        payload_block_suffix=PARTICLE_SUFFIX,
        func_read_payload_block=read_particle_block,
    )


PARTICLE_SUFFIX = ".par.x7.float32"


def read_particle_block(tar, tarinfo):
    return event_tape.read_payload_block(tar=tar, tarinfo=tarinfo, shape_1=7)


def decode_particle_id(f4):
    """
    particle description encoded as:
    part. id×1000 + hadr. generation [94] × 10 + no. of obs. level
    [for additional muon information: part. id×1000 + hadr. generation 95 ]
    """
    particle_id = int(f4 // 1000)
    return particle_id


def dat_to_tape(dat_path, tape_path):
    with open(dat_path, "rb") as df, tape.ParticleTapeWriter(
        tape_path
    ) as evttape:
        with RunReader(df) as run:
            evttape.write_runh(run.runh)

            for event in run:
                evth, particle_reader = event
                evttape.write_evth(evth)

                for block in particle_reader:
                    evttape.write_payload(block)


def assert_dat_is_valid(dat_path):
    iii = rundict.read_rundict(dat_path)
    rundict.write_rundict(dat_path + ".back", iii)
    bbb = rundict.read_rundict(dat_path + ".back")
    rundict.assert_rundict_equal(iii, bbb)
