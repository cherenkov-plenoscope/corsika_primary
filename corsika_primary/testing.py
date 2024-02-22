import numpy as np
import subprocess
import os
import copy
import glob
import spherical_coordinates
import tempfile
from . import I
from . import random
from . import steering
from . import particles
from . import cherenkov


class TmpDebugDir:
    def __init__(self, debug_dir, suffix=None, prefix="corsika_primary"):
        if debug_dir:
            self.debug = True
            self.handle = None
            self.name = os.path.join(debug_dir, suffix)
            os.makedirs(self.name, exist_ok=True)
        else:
            self.debug = False
            self.tmp_dir_handle = tempfile.TemporaryDirectory(
                prefix=prefix, suffix=suffix
            )
            self.name = self.tmp_dir_handle.name

    def cleanup_when_no_debug(self):
        if not self.debug:
            self.tmp_dir_handle.cleanup()


def eventio_to_simpleio(
    merlict_eventio_converter, eventio_path, simpleio_path
):
    rc = subprocess.call(
        [
            merlict_eventio_converter,
            "-i",
            eventio_path,
            "-o",
            simpleio_path,
        ]
    )
    assert rc == 0


class SimpleIoRun:
    def __init__(self, path):
        """
        Parameters
        ----------
        path        The path to the directory representing the run.
        """
        self.path = os.path.abspath(path)
        if not os.path.isdir(self.path):
            raise NotADirectoryError(self.path)

        with open(os.path.join(path, "corsika_run_header.bin"), "rb") as f:
            self.runh = np.frombuffer(f.read(), dtype=np.float32)

        self.event_ids = []
        for p in glob.glob(os.path.join(path, "*")):
            if os.path.isdir(p) and os.path.basename(p).isdigit():
                self.event_ids.append(int(os.path.basename(p)))
        self.event_ids = np.array(self.event_ids)
        self.event_ids.sort()
        self.next_event_id = self.event_ids[0]

    def __next__(self):
        event_path = os.path.join(self.path, str(self.next_event_id))
        if not os.path.isdir(event_path):
            raise StopIteration

        evth_path = os.path.join(event_path, "corsika_event_header.bin")
        with open(evth_path, "rb") as f:
            evth = np.frombuffer(f.read(), dtype=np.float32)

        bunches_path = os.path.join(
            event_path, "air_shower_photon_bunches.bin"
        )
        with open(bunches_path, "rb") as f:
            bunches = np.frombuffer(f.read(), dtype=np.float32)

        assert bunches.shape[0] % 8 == 0
        num_bunches = bunches.shape[0] // 8
        bunches = bunches.reshape((num_bunches, 8))

        self.next_event_id += 1
        return (evth, bunches)

    def __iter__(self):
        return self

    def __exit__(self):
        pass

    def __repr__(self):
        out = self.__class__.__name__ + "(path={:s})".format(self.path)
        return out


def parse_random_seeds_from_corsika_stdout(stdout):
    """
    Returns a list of random-number-generator states at the begin of each
    event.
    Does not contain all events. CORSIKA does not print this for all events.
    Only use this when CORSIKA's Cherenkov-output is broken.

    parameters
    ----------
    stdout : str
        CORSIKA's stdout.
    """
    events = []
    MARKER = " AND RANDOM NUMBER GENERATOR AT BEGIN OF EVENT :"
    lines = stdout.split("\n")
    idx = 0
    while idx < len(lines):
        if MARKER in lines[idx]:
            _seeds = [None] * random.seed.NUM_RANDOM_SEQUENCES
            _calls = [None] * random.seed.NUM_RANDOM_SEQUENCES
            _billions = [None] * random.seed.NUM_RANDOM_SEQUENCES
            event_number = int(lines[idx][49:57])
            assert len(events) + 1 == event_number

            for seq in np.arange(0, random.seed.NUM_RANDOM_SEQUENCES):
                is_sequence = False
                while idx < len(lines) and not is_sequence:
                    idx += 1
                    match = " SEQUENCE =  {:d}  SEED =".format(seq + 1)
                    is_sequence = str.find(lines[idx], match) == 0
                _seeds[seq] = int(lines[idx][22:33])
                _calls[seq] = int(lines[idx][41:52])
                _billions[seq] = int(lines[idx][63:73])

            state = []
            for seq in np.arange(0, random.seed.NUM_RANDOM_SEQUENCES):
                state.append(
                    {
                        "SEED": np.int32(_seeds[seq]),
                        "CALLS": np.int32(_calls[seq]),
                        "BILLIONS": np.int32(_billions[seq]),
                    }
                )
            events.append(state)
        idx += 1
    return events


def parse_num_bunches_from_corsika_stdout(stdout):
    """
    Returns the number of bunches, not photons of each event.
    Does not contain all events. CORSIKA does not print this for all events.
    Only use this when CORSIKA's Cherenkov-output is broken.

    parameters
    ----------
    stdout : str
        CORSIKA's stdout.
    """
    marker = " Total number of photons in shower:"
    nums = []
    lines = stdout.split("\n")
    for ll in range(len(lines)):
        pos = lines[ll].find(marker)
        if pos == 0:
            work_line = lines[ll][len(marker) : -1]
            pos_2nd_in = work_line.find("in")
            work_line = work_line[pos_2nd_in + 2 : -len("bunch") - 1]
            nums.append(int(float(work_line)))
    return nums


def stdout_ends_with_end_of_run_marker(stdout):
    """
    According to CORSIKA-author Heck, this is the only sane way to check
    whether CORSIKA has finished.
    """
    lines = stdout.split("\n")
    if len(lines) < 2:
        return False

    second_last_line = lines[-2]
    MARKER = (
        " "
        + "=========="
        + " END OF RUN "
        + "================================================"
    )
    if MARKER in second_last_line:
        return True
    else:
        return False


def write_hashes(path, hashes):
    with open(path, "wt") as f:
        for event_id in hashes:
            s = "{:d},{:s}\n".format(event_id, hashes[event_id])
            f.write(s)


def read_hashes(path):
    hashes = {}
    with open(path, "rt") as f:
        for line in str.splitlines(f.read()):
            event_id_str, h_str = str.split(line, ",")
            hashes[int(event_id_str)] = h_str
    return hashes


def write_seeds(path, seeds):
    with open(path, "wt") as f:
        f.write(random.seed.dumps(seeds=seeds))


def read_seeds(path):
    with open(path, "rt") as f:
        return random.seed.loads(s=f.read())


def make_example_steering_for_particle_output():
    ste = copy.deepcopy(steering.EXAMPLE)

    f8 = np.float64

    ste["run"]["energy_range"] = {
        "start_GeV": f8(100.0),
        "stop_GeV": f8(200.0),
    }
    ste["primaries"] = [
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
    return ste


def draw_cherenkov_bunches_from_point_source(
    instrument_sphere_x_cm,
    instrument_sphere_y_cm,
    instrument_sphere_radius_cm,
    source_azimuth_rad,
    source_zenith_rad,
    source_distance_to_instrument_cm,
    prng,
    size=100,
    bunch_size_low=0.9,
    bunch_size_high=1.0,
    wavelength_low_nm=350,
    wavelength_high_nm=550,
    speed_of_ligth_cm_per_ns=29.9792458,
    observation_level_asl_cm=0.0,
):
    """
    KIT-CORSIKA coordinate-system
    -----------------------------

    *                   /| z-axis                                              *
    *                   |                                                      *
    *                   || p                                                   *
    *                   | | a                                                  *
    *                   |  | r                                                 *
    *                   |   | t                                                *
    *                   |    | i                                               *
    *                   |     | c                                              *
    *                   |      | l                                             *
    *                   |       | e                                            *
    *                   |        |                                             *
    *                   |  theta  | m                                          *
    *                   |       ___| o                                         *
    *                   |___----    | m      ___                               *
    *                   |            | e       /| y-axis (west)                *
    *                   |             | n    /                                 *
    *                   |              | t /                                   *
    *                   |               |/u                                    *
    *                   |              / | m                                   *
    *                   |            /    |                                    *
    *                   |          /       |                                   *
    *                   |        /__________|                                  *
    *                   |      /      ___---/                                  *
    *                   |    /   __---    /                                    *
    *                   |  /__--- phi | /                                      *
    *   ________________|/--__________/______| x-axis (north)                  *
    *                  /|                    /                                 *
    *                /  |                                                      *
    *              /    |                                                      *
    *            /                                                             *
    *                                                                          *
    *                                                                          *
        Extensive Air Shower Simulation with CORSIKA, Figure 1, page 114
        (Version 7.6400 from December 27, 2017)

        Direction-cosines:

        u = sin(theta) * cos(phi)
        v = sin(theta) * sin(phi)

        The zenith-angle theta opens relative to the negative z-axis.

        It is the momentum of the Cherenkov-photon, which is pointing
        down towards the observation-plane.

    """
    assert speed_of_ligth_cm_per_ns > 0
    assert bunch_size_low >= 0
    assert bunch_size_high >= bunch_size_low
    assert wavelength_low_nm > 0.0
    assert wavelength_high_nm >= wavelength_low_nm
    assert size >= 0
    assert instrument_sphere_radius_cm >= 0.0

    BUNCH = I.BUNCH
    b = np.zeros(shape=(size, BUNCH.NUM_FLOAT32), dtype=np.float32)

    source_impact_direction = np.array(
        spherical_coordinates.az_zd_to_cx_cy_cz(
            azimuth_rad=source_azimuth_rad,
            zenith_rad=source_zenith_rad,
        )
    )

    instrument_position = np.array(
        [instrument_sphere_x_cm, instrument_sphere_y_cm, 0.0]
    )

    source_position = (
        instrument_position
        + source_distance_to_instrument_cm * source_impact_direction
    )

    for i in range(size):
        px_cm, py_cm = random.distributions.draw_x_y_in_disc(
            prng=prng, radius=instrument_sphere_radius_cm
        )
        impact = np.array(
            [
                px_cm + instrument_sphere_x_cm,
                py_cm + instrument_sphere_y_cm,
                0.0,
            ]
        )
        b[i, BUNCH.X_CM] = impact[0]
        b[i, BUNCH.Y_CM] = impact[1]

        photon_path = -source_position + impact
        photon_path_length_cm = np.linalg.norm(photon_path)
        photon_momentum = photon_path / photon_path_length_cm

        b[i, BUNCH.UX_1] = photon_momentum[0]
        b[i, BUNCH.VY_1] = photon_momentum[1]

        b[i, BUNCH.TIME_NS] = photon_path_length_cm / speed_of_ligth_cm_per_ns
        b[i, BUNCH.EMISSOION_ALTITUDE_ASL_CM] = (
            source_position[2] + observation_level_asl_cm
        )

    b[:, BUNCH.BUNCH_SIZE_1] = prng.uniform(
        low=bunch_size_low, high=bunch_size_high, size=size
    )
    b[:, BUNCH.WAVELENGTH_NM] = prng.uniform(
        low=wavelength_low_nm, high=wavelength_high_nm, size=size
    )

    return b


def printf_histogram(
    x,
    bin_edges=None,
    bin_count_fmt="{: 6.1f}",
    bin_edge_fmt="{: 6.1f}",
    counts_max=None,
    num_rows=6,
):
    bin_counts = np.histogram(x, bins=bin_edges)[0]

    if counts_max is None:
        counts_max = np.max(bin_counts)
    counts_per_row = counts_max / num_rows

    s = ""
    for rr in np.arange(num_rows, -1, -1):
        s += "   "
        for bb in range(len(bin_counts)):
            upper_row_counts_threshold = rr * counts_per_row
            lower_row_counts_threshold = (rr - 1) * counts_per_row

            if (
                upper_row_counts_threshold
                >= bin_counts[bb]
                > lower_row_counts_threshold
            ):
                s += (
                    ("." + bin_count_fmt + ".")
                    .format(bin_counts[bb])
                    .replace(" ", "_")
                )
            elif upper_row_counts_threshold < bin_counts[bb]:
                s += "|       |"
            else:
                s += "         "
        s += "\n"

    if bin_edges is not None:
        for ee in range(len(bin_edges)):
            s += (bin_edge_fmt + "   ").format(bin_edges[ee])
    return s


def print_cherenkov_run(
    path,
    x_bin_edges=np.linspace(-100, 100, 11),
    cx_bin_edges_deg=np.linspace(-10, 10, 11),
):
    run = cherenkov.CherenkovEventTapeReader(path)

    for event in run:
        evth, cerreader = event
        cer = np.concatenate([b for b in cerreader])

        run_id = int(evth[I.EVTH.RUN_NUMBER])
        event_id = int(evth[I.EVTH.EVENT_NUMBER])
        energy_GeV = evth[I.EVTH.TOTAL_ENERGY_GEV]
        num_cer = len(cer)
        size_cer = np.sum(cer[:, I.BUNCH.BUNCH_SIZE_1])
        x = 1e-2 * np.median(cer[:, I.BUNCH.X_CM])
        y = 1e-2 * np.median(cer[:, I.BUNCH.Y_CM])
        r_max = 1e-2 * np.max(
            np.hypot(cer[:, I.BUNCH.X_CM], cer[:, I.BUNCH.Y_CM])
        )

        cx = np.rad2deg(np.median(cer[:, I.BUNCH.CX_RAD]))
        cy = np.rad2deg(np.median(cer[:, I.BUNCH.CY_RAD]))

        cr_max = np.rad2deg(
            np.max(np.hypot(cer[:, I.BUNCH.CX_RAD], cer[:, I.BUNCH.CY_RAD]))
        )

        print(
            "run:{: 6d}, event:{: 6d}, energy:{: 8.1f}GeV, num:{: 6d}, size:{: 6.0f}, x:{: 6.1f}m, y:{: 6.1f}m, r-max:{: 6.1f}m, cx:{: 6.1f}deg, cy:{: 6.1f}deg, cr-max:{: 6.1f}deg".format(
                run_id,
                event_id,
                energy_GeV,
                num_cer,
                size_cer,
                x,
                y,
                r_max,
                cx,
                cy,
                cr_max,
            )
        )
        print("x-histogram / m")
        print("---------------")
        print(
            printf_histogram(
                x=1e-2 * cer[:, I.BUNCH.X_CM],
                bin_edges=x_bin_edges,
                bin_count_fmt="{: 7d}",
            )
        )

        print("y-histogram / m")
        print("---------------")
        print(
            printf_histogram(
                x=1e-2 * cer[:, I.BUNCH.Y_CM],
                bin_edges=x_bin_edges,
                bin_count_fmt="{: 7d}",
            )
        )

        print("cx-histogram / DEG")
        print("------------------")
        print(
            printf_histogram(
                x=np.rad2deg(cer[:, I.BUNCH.CX_RAD]),
                bin_edges=cx_bin_edges_deg,
                bin_count_fmt="{: 7d}",
            )
        )
        print("cy-histogram / DEG")
        print("------------------")
        print(
            printf_histogram(
                x=np.rad2deg(cer[:, I.BUNCH.CY_RAD]),
                bin_edges=cx_bin_edges_deg,
                bin_count_fmt="{: 7d}",
            )
        )
