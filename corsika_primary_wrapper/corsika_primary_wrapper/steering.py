import numpy as np
import io
import shutil
import tarfile
import os
from . import version

i8 = np.int64
f8 = np.float64

NUM_BYTES_PRIMARY_STEERING = 5 * 8 + 12 * 4
NUM_BYTES_RUN_STEERING = 8 * 8
ENERGY_LIMIT_OVERHEAD = 0.01
PRIMARY_BYTES_FILENAME_IN_CORSIKA_RUN_DIR = "primary_bytes.5xf8_12xi4"

HEADER = "{:<23}\n".format("CORSIKA-PRIMARY-MOD")
HEADER += "{:<23}\n".format("BY S. A. Mueller")
HEADER += "{:<23}\n".format("VERSION " + version.__version__)
HEADER = HEADER.encode()
NUM_BYTES_HEADER = 24 * 3
assert len(HEADER) == NUM_BYTES_HEADER


def make_simple_seed(seed):
    """
    Returns the explicit random-seed for a single event.
    It steers 4 sequences.
    This simple seed follows the default seeding used in CORSIKA where each
    sequence has SEED_OF_LAST_SEQUENCE + 1.
    CORSIKA stores this as int32, so we must respect the limits.
    """
    assert seed % 1 == 0, "The seed must be an integer."
    assert seed < 2 ** 31, "The seed must fit into int32."
    i4 = np.int32
    return [
        {"SEED": i4(seed), "CALLS": i4(0), "BILLIONS": i4(0)},
        {"SEED": i4(seed + 1), "CALLS": i4(0), "BILLIONS": i4(0)},
        {"SEED": i4(seed + 2), "CALLS": i4(0), "BILLIONS": i4(0)},
        {"SEED": i4(seed + 3), "CALLS": i4(0), "BILLIONS": i4(0)},
    ]


EXAMPLE = {
    "run": {
        "run_id": i8(1),
        "event_id_of_first_event": i8(1),
        "observation_level_asl_m": f8(2300),
        "earth_magnetic_field_x_muT": f8(12.5),
        "earth_magnetic_field_z_muT": f8(-25.9),
        "atmosphere_id": i8(10),
        "energy_range": {"start_GeV": f8(1.0), "stop_GeV": f8(20.0)},
    },
    "primaries": [
        {
            "particle_id": i8(1),
            "energy_GeV": f8(1.32),
            "zenith_rad": f8(0.0),
            "azimuth_rad": f8(0.0),
            "depth_g_per_cm2": f8(0.0),
            "random_seed": make_simple_seed(0),
        },
        {
            "particle_id": i8(1),
            "energy_GeV": f8(1.52),
            "zenith_rad": f8(0.1),
            "azimuth_rad": f8(0.2),
            "depth_g_per_cm2": f8(3.6),
            "random_seed": make_simple_seed(1),
        },
        {
            "particle_id": i8(1),
            "energy_GeV": f8(11.4),
            "zenith_rad": f8(0.1),
            "azimuth_rad": f8(0.25),
            "depth_g_per_cm2": f8(102.2),
            "random_seed": make_simple_seed(2),
        },
    ],
}


def assert_values(steering_dict, energy_overhead=1.01):
    run = steering_dict["run"]
    primaries = steering_dict["primaries"]
    int32_limit = 2 ** 31

    # energy
    assert run["energy_range"]["start_GeV"] > 0
    assert run["energy_range"]["stop_GeV"] > 0
    assert run["energy_range"]["start_GeV"] < run["energy_range"]["stop_GeV"]

    assert energy_overhead >= 1.0
    eoh = energy_overhead
    for p in primaries:
        assert run["energy_range"]["start_GeV"] < p["energy_GeV"] / eoh
        assert run["energy_range"]["stop_GeV"] > p["energy_GeV"] * eoh

        for sequence in p["random_seed"]:
            assert sequence["SEED"] < int32_limit
            assert sequence["CALLS"] < int32_limit
            assert sequence["BILLIONS"] < int32_limit


def assert_dtypes_in_obj(obj, dtype):
    if isinstance(dtype, list):
        for idx in range(len(dtype)):
            assert_dtypes_in_obj(obj[idx], dtype[idx])
    elif isinstance(dtype, dict):
        for key in dtype:
            assert_dtypes_in_obj(obj=obj[key], dtype=dtype[key])
    elif hasattr(dtype, "dtype"):
        assert obj.dtype.str == dtype.dtype.str
    else:
        raise RuntimeError()


def assert_dtypes_run_dict(run_dict):
    assert_dtypes_in_obj(obj=run_dict, dtype=EXAMPLE["run"])


def assert_dtypes_primary_dict(primary_dict):
    assert_dtypes_in_obj(obj=primary_dict, dtype=EXAMPLE["primaries"][0])


def make_run_card_str(steering_dict, output_path):
    """
    Make steering card-st for CORSIKA. The card contains all steering for
    the run which is the same for each event.
    """
    run = steering_dict["run"]
    primaries = steering_dict["primaries"]
    assert_dtypes_run_dict(run)
    for prm in primaries:
        assert_dtypes_primary_dict(prm)
    M_TO_CM = 1e2
    card = "\n".join(
        [
            "RUNNR {:d}".format(run["run_id"]),
            "EVTNR {:d}".format(run["event_id_of_first_event"]),
            "PRMPAR 1",
            "ERANGE {e_min:.6E} {e_max:.6E}".format(
                e_min=run["energy_range"]["start_GeV"],
                e_max=run["energy_range"]["stop_GeV"],
            ),
            "OBSLEV {:.6E}".format(M_TO_CM * run["observation_level_asl_m"]),
            "MAGNET {x:.6E} {z:.6E}".format(
                x=run["earth_magnetic_field_x_muT"],
                z=run["earth_magnetic_field_z_muT"],
            ),
            "MAXPRT 1",
            "PAROUT F F",
            "ATMOSPHERE {:d} T".format(run["atmosphere_id"]),
            "CWAVLG 250 700",
            "CERQEF F T F",
            "CERSIZ 1.",
            "CERFIL F",
            "TSTART T",
            "NSHOW {:d}".format(len(primaries)),
            "TELFIL {:s}".format(output_path),
            "EXIT",
        ]
    )
    return card


def _read(f, dtype_str):
    """
    Read a single value of specific dtype from a stream.
    """
    num_bytes = int(dtype_str[-1])
    arr = np.frombuffer(f.read(num_bytes), dtype=dtype_str)
    assert arr.shape[0] == 1
    return arr[0]


def primary_dict_to_bytes(primary_dict):
    """
    Returns bytes for our CORSIKA-primary-mod.

    See also: primary_bytes_to_dict
    """
    prmdic = primary_dict
    assert_dtypes_primary_dict(prmdic)
    with io.BytesIO() as f:
        f.write(prmdic["particle_id"].tobytes())
        f.write(prmdic["energy_GeV"].tobytes())
        f.write(prmdic["zenith_rad"].tobytes())
        f.write(prmdic["azimuth_rad"].tobytes())
        f.write(prmdic["depth_g_per_cm2"].tobytes())
        for seq in range(4):
            for key in ["SEED", "CALLS", "BILLIONS"]:
                f.write(prmdic["random_seed"][seq][key].tobytes())
        f.seek(0)
        return f.read()


def primary_bytes_to_dict(primary_bytes):
    """
    Return the primary_dict reconstructed from bytes.

    See also: primary_dict_to_bytes
    """
    prm = {}
    PRM = EXAMPLE["primaries"][0]
    assert len(primary_bytes) == NUM_BYTES_PRIMARY_STEERING
    with io.BytesIO(primary_bytes) as f:
        prm["particle_id"] = _read(f, PRM["particle_id"].dtype.str)
        prm["energy_GeV"] = _read(f, PRM["energy_GeV"].dtype.str)
        prm["zenith_rad"] = _read(f, PRM["zenith_rad"].dtype.str)
        prm["azimuth_rad"] = _read(f, PRM["azimuth_rad"].dtype.str)
        prm["depth_g_per_cm2"] = _read(f, PRM["depth_g_per_cm2"].dtype.str)
        prm["random_seed"] = []
        for n in range(4):
            seq = {}
            for key in ["SEED", "CALLS", "BILLIONS"]:
                seq[key] = _read(f, PRM["random_seed"][n][key].dtype.str)
            prm["random_seed"].append(seq)
    assert_dtypes_primary_dict(prm)
    return prm


def primary_dicts_to_bytes(primary_dicts):
    """
    primary_dicts : list of primary dicts.
    """
    with io.BytesIO() as f:
        for primary_dict in primary_dicts:
            f.write(primary_dict_to_bytes(primary_dict))
        f.seek(0)
        return f.read()


def primary_bytes_to_dicts(primary_bytes):
    """
    primary_bytes : multiple primary dicts.
    """
    assert len(primary_bytes) % NUM_BYTES_PRIMARY_STEERING == 0
    num_primaries = len(primary_bytes) // NUM_BYTES_PRIMARY_STEERING
    primary_dicts = []
    with io.BytesIO(primary_bytes) as f:
        for idx in range(num_primaries):
            prm_bytes = f.read(NUM_BYTES_PRIMARY_STEERING)
            prm_dict = primary_bytes_to_dict(prm_bytes)
            primary_dicts.append(prm_dict)
    return primary_dicts


def run_dict_to_bytes(run_dict):
    rd = run_dict
    assert_dtypes_run_dict(rd)
    with io.BytesIO() as f:
        f.write(rd["run_id"].tobytes())
        f.write(rd["event_id_of_first_event"].tobytes())
        f.write(rd["observation_level_asl_m"].tobytes())
        f.write(rd["earth_magnetic_field_x_muT"].tobytes())
        f.write(rd["earth_magnetic_field_z_muT"].tobytes())
        f.write(rd["atmosphere_id"].tobytes())
        f.write(rd["energy_range"]["start_GeV"].tobytes())
        f.write(rd["energy_range"]["stop_GeV"].tobytes())
        f.seek(0)
        return f.read()


def run_bytes_to_dict(run_bytes):
    rud = {}
    RUN = EXAMPLE["run"]
    assert len(run_bytes) == NUM_BYTES_RUN_STEERING
    with io.BytesIO(run_bytes) as f:
        rud["run_id"] = _read(f, RUN["run_id"].dtype.str)
        rud["event_id_of_first_event"] = _read(f, RUN["event_id_of_first_event"].dtype.str)
        rud["observation_level_asl_m"] = _read(f, RUN["observation_level_asl_m"].dtype.str)
        rud["earth_magnetic_field_x_muT"] = _read(f, RUN["earth_magnetic_field_x_muT"].dtype.str)
        rud["earth_magnetic_field_z_muT"] = _read(f, RUN["earth_magnetic_field_z_muT"].dtype.str)
        rud["atmosphere_id"] = _read(f, RUN["atmosphere_id"].dtype.str)
        rud["energy_range"] = {}
        rud["energy_range"]["start_GeV"] = _read(f, RUN["energy_range"]["start_GeV"].dtype.str)
        rud["energy_range"]["stop_GeV"] = _read(f, RUN["energy_range"]["stop_GeV"].dtype.str)
    assert_dtypes_run_dict(rud)
    return rud


def primary_bytes_by_idx(primary_bytes, idx):
    bstart = idx * NUM_BYTES_PRIMARY_STEERING
    bstop = (idx + 1) * NUM_BYTES_PRIMARY_STEERING
    return primary_bytes[bstart: bstop]


def write_steerings(runs, path):
    with tarfile.open(path + ".tmp", "w") as tarfout:
        for run_id in runs:
            run = runs[run_id]
            assert run_id == run["run"]["run_id"]
            with io.BytesIO() as buff:
                buff.write(HEADER)
                buff.write(run_dict_to_bytes(run["run"]))
                for primary_dict in run["primaries"]:
                    buff.write(primary_dict_to_bytes(primary_dict))
                buff.seek(0)
                _tar_write(
                    tarfout=tarfout,
                    path="{:09d}.steering.bin".format(run_id),
                    payload=buff.read(),
                )
    shutil.move(path + ".tmp", path)


def read_steerings(path):
    runs = {}
    with tarfile.open(path, "r") as tarfin:
        while True:
            tarinfo = tarfin.next()
            if tarinfo is None:
                break

            run_id_str, ss, bb = str.split(tarinfo.name, ".")
            run_id = int(run_id_str)
            assert ss == "steering"
            assert bb == "bin"
            num_bytes_primaries = (
                tarinfo.size
                - NUM_BYTES_HEADER
                - NUM_BYTES_RUN_STEERING
            )
            assert num_bytes_primaries >= 0
            assert num_bytes_primaries % NUM_BYTES_PRIMARY_STEERING == 0
            num_primaries = num_bytes_primaries // NUM_BYTES_PRIMARY_STEERING

            with tarfin.extractfile(tarinfo) as f:
                header = f.read(NUM_BYTES_HEADER).decode()
                version_line = str.split(header, "\n")[2]
                version_str = str.split(version_line, " ")[1]
                if version_str != version.__version__:
                    print("WARNING, version mismatch.")
                run_bytes = f.read(NUM_BYTES_RUN_STEERING)
                primary_bytes = f.read(num_bytes_primaries)

                run = {}
                run["run"] = run_bytes_to_dict(run_bytes)
                run["primaries"] = []
                for idx in range(num_primaries):
                    run["primaries"].append(
                        primary_bytes_to_dict(
                            primary_bytes_by_idx(
                                primary_bytes=primary_bytes,
                                idx=idx
                            )
                        )
                    )
                assert run["run"]["run_id"] == run_id
                runs[run_id] = run
    return runs


def _tar_write(tarfout, path, payload):
    tarinfo = tarfile.TarInfo()
    tarinfo.name = path
    tarinfo.size = len(payload)
    with io.BytesIO() as f:
        f.write(payload)
        f.seek(0)
        tarfout.addfile(tarinfo=tarinfo, fileobj=f)