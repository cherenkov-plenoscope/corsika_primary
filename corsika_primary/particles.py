import numpy as np


class RunReader:
    def __init__(self, path, num_offset_bytes=4):
        """
        """
        self.block_reader = BlockReader(
            path=path, num_offset_bytes=num_offset_bytes
        )
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

    def __iter__(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.block_reader.close()

    def __repr__(self):
        out = "{:s}(path={:s})".format(
            self.__class__.__name__, self.block_reader.path
        )
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
        out = "{:s}(path={:s})".format(
            self.__class__.__name__, self.block_reader.path
        )
        return out


class BlockReader:
    def __init__(self, path, num_offset_bytes=4):
        """
        """
        self.path = path
        self.file = open(self.path, "rb")
        self.num_bytes_per_block = 273 * 4
        self.stuff_before_runh = self.file.read(num_offset_bytes)

    def __next__(self):
        block_bytes = self.file.read(self.num_bytes_per_block)
        if len(block_bytes) == self.num_bytes_per_block:
            block_f32 = np.frombuffer(block_bytes, dtype=np.float32)
            return block_f32
        else:
            raise StopIteration

    def close(self):
        self.file.close()

    def __iter__(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def __repr__(self):
        out = "{:s}(path={:s})".format(self.__class__.__name__, self.path)
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
    def __init__(self, path, num_offset_bytes=4):
        self.path = path
        self.file = open(path, "wb")
        self._has_runh = False
        self._event_has_evth = False
        self._event_has_evte = False
        self._has_rune = False
        self.particle_block_size = 0
        self.stuff_before_runh = b"\x94Y\x00\x00"
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
            num_padding_all_zero_particles == 0
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

    def close(self):
        self.file.close()

    def __iter__(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def __repr__(self):
        out = "{:s}(path={:s})".format(self.__class__.__name__, self.path)
        return out


def read_rundict(path):
    rrr = {}
    with RunReader(path=path) as run:
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
    with RunWriter(path=path + ".back") as out:
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
