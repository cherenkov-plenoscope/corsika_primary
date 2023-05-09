import numpy as np
from . import event_tape

DAT_FILE_TEMPLATE = "DAT{runnr:06d}"


class RunReader:
    def __init__(self, stream, num_offset_bytes=4):
        """
        """
        self.block_reader = BlockReader(stream=stream)
        self.runh = self.block_reader.__next__()
        assert self.runh[0].tobytes() == b"RUNH", "Expected RUNH"

    def __next__(self):
        block = self.block_reader.__next__()

        if block[0].tobytes() == b"RUNE":
            self.rune = block

            for trailing_zero_block in self.block_reader:
                assert np.all(trailing_zero_block == np.float32(0.0))

            raise StopIteration
        else:
            evth = block
            assert evth[0].tobytes() == b"EVTH", "Expected EVTH"
            return evth, ParticleBlockReader(block_reader=self.block_reader)

    def close(self):
        self.block_reader.close()

    def __iter__(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def __repr__(self):
        out = "{:s}()".format(self.__class__.__name__)
        return out


class ParticleBlockReader:
    def __init__(self, block_reader):
        """
        """
        self.block_reader = block_reader

    def __next__(self):
        block = self.block_reader.__next__()

        if block[0].tobytes() == b"EVTE":
            self.evte = block
            raise StopIteration
        else:
            matrix = block.reshape((39, 7))
            is_particle = matrix[:, 0] != np.float32(0.0)
            particle_matrix = matrix[is_particle]
            return particle_matrix

    def __iter__(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        pass

    def __repr__(self):
        out = "{:s}()".format(self.__class__.__name__)
        return out


def decode_particle_id(f4):
    """
    particle description encoded as:
    part. id×1000 + hadr. generation [94] × 10 + no. of obs. level
    [for additional muon information: part. id×1000 + hadr. generation 95 ]
    """
    particle_id = int(f4 // 1000)
    return particle_id


class RunWriter:
    def __init__(self, stream, num_offset_bytes=4):
        self.file = stream
        self._has_runh = False
        self._event_has_evth = False
        self._event_has_evte = False
        self._has_rune = False
        self.particle_block_size = 0
        self.stuff_before_runh = b"\x94Y\x00\x00"
        self.stuff_after_zero_blocks = self.stuff_before_runh
        self.num_trailing_zero_blocks = 10
        self.file.write(self.stuff_before_runh)

    def write_runh(self, runh):
        self.assert_is_valid_head(head=runh, marker=b"RUNH")
        assert not self._has_rune
        assert not self._has_runh
        self._has_runh = True
        self.file.write(runh.tobytes())

    def write_evth(self, evth):
        self.assert_is_valid_head(head=evth, marker=b"EVTH")
        assert not self._has_rune
        assert self._has_runh
        assert not self._event_has_evth
        self._event_has_evth = True
        self._event_has_evte = False
        self.file.write(evth.tobytes())

    def write_evte(self, evte):
        self.assert_is_valid_head(head=evte, marker=b"EVTE")
        assert not self._has_rune
        assert self._has_runh
        assert not self._event_has_evte
        self._event_has_evte = True
        self._event_has_evth = False

        if 0 == self.particle_block_size:
            num_padding_all_zero_particles = 0
        else:
            num_padding_all_zero_particles = 39 - self.particle_block_size

        for i in range(num_padding_all_zero_particles):
            self.write_particle(np.zeros(7, dtype=np.float32))

        assert self.particle_block_size == 0

        self.file.write(evte.tobytes())

    def write_rune(self, rune):
        self.assert_is_valid_head(head=rune, marker=b"RUNE")
        assert not self._has_rune
        self._has_rune = True
        self.file.write(rune.tobytes())
        self.write_trailing_zero_blocks()
        self.file.write(self.stuff_after_zero_blocks)

    def write_particle(self, particle):
        assert particle.shape == (7,)
        assert particle.dtype == np.float32

        self.particle_block_size += 1
        if self.particle_block_size == 39:
            self.particle_block_size = 0
        self.file.write(particle.tobytes())

    def assert_is_valid_head(self, head, marker):
        assert head[0].tobytes() == marker
        assert head.shape == (273,)
        assert head.dtype == np.float32

    def write_trailing_zero_blocks(self):
        zero_block = np.zeros(273, dtype=np.float32)
        for i in range(self.num_trailing_zero_blocks):
            self.file.write(zero_block.tobytes())

    def close(self):
        self.file.close()

    def __iter__(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def __repr__(self):
        out = "{:s}()".format(self.__class__.__name__)
        return out


def read_rundict(path, num_offset_bytes=4):
    rrr = {}
    with open(path, "rb") as istream:
        with RunReader(
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


def write_rundict(path, rrr):
    with open(path, "wb") as ostream:
        with RunWriter(stream=ostream) as out:
            out.write_runh(rrr["RUNH"])
            for eee in rrr["events"]:
                out.write_evth(eee["EVTH"])
                for ppp in eee["particles"]:
                    out.write_particle(ppp)
                out.write_evte(eee["EVTE"])
            out.write_rune(rrr["RUNE"])


def assert_rundict_equal(rrr, bbb):
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
        np.testing.assert_array_equal(eeer["EVTE"], eeeb["EVTE"])
    np.testing.assert_array_equal(rrr["RUNE"], bbb["RUNE"])


def find_markers(
    stream, marker=[b"RUNH", b"EVTH", b"EVTE", b"RUNE", b"\x94Y\x00\x00"],
):
    out = []
    i = 0
    while True:
        b4 = stream.read(4)
        if b4 == b"":
            break
        if b4 in marker:
            find = (b4, i)
            out.append(find)
        i += 1
    return out


class BlockReader:
    """
    According to the CORSIKA manual 7.56 the particle-output is structured
    into blocks of 273xfloat32s.
    But for some reason there is this ***** in the stream: \x94Y\x00\x00
    I have no idea why.
    This reader tries to work around this.
    """

    def __init__(self, stream):
        self.file = stream
        self.b1_marker = b"\x94Y\x00\x00"

    def __next__(self):
        self.b1 = self.file.read(4)

        N = 300
        n = 0
        while self.b1 == self.b1_marker:
            self.b1 = self.file.read(4 * 1)
            n += 1
            assert n <= N, "Can not read this."

        if len(self.b1) < 4:
            raise StopIteration

        b272 = self.file.read(4 * 272)
        if len(b272) < 4 * 272:
            raise StopIteration

        f1 = np.frombuffer(self.b1, dtype=np.float32)
        f272 = np.frombuffer(b272, dtype=np.float32)

        block273 = np.zeros(273, dtype=np.float32)
        block273[0] = f1[0]
        block273[1:] = f272
        return block273

    def close(self):
        pass

    def __iter__(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def __repr__(self):
        out = "{:s}()".format(self.__class__.__name__)
        return out


def assert_valid(particle_path):
    iii = read_rundict(particle_path)
    write_rundict(particle_path + ".back", iii)
    bbb = read_rundict(particle_path + ".back")
    assert_rundict_equal(iii, bbb)


def ParticleTapeWriter(path, buffer_capacity=1000 * 1000):
    """
    Write an EventTape. Add RUNH, EVTH, and cherenkov-bunches.

    path : str
        Path to event-tape file.
    buffer_capacity : int
        Buffer-size in cherenkov-bunches.
    """
    PATRICLE_BLOCK_FILENAME = (
        "{run_number:09d}/{event_number:09d}/{block_number:09d}.par.x7.float32"
    )
    return event_tape.TapeWriter(
        path=path,
        payload_shape_1=7,
        block_filename_template=PATRICLE_BLOCK_FILENAME,
        buffer_capacity=buffer_capacity * 7,
    )


def dat_to_tape(dat_path, tape_path):
    with open(dat_path, "rb") as df, ParticleTapeWriter(tape_path) as evttape:
        with RunReader(df) as run:
            evttape.write_runh(run.runh)

            for event in run:
                evth, particle_reader = event
                evttape.write_evth(evth)

                for block in particle_reader:
                    evttape.write_payload(block)
