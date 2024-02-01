import pytest
import corsika_primary as cpw
import inspect
import numpy as np
import tempfile
import os

i4 = np.int32
i8 = np.int64
f8 = np.float64


@pytest.fixture()
def debug_dir(pytestconfig):
    return pytestconfig.getoption("debug_dir")


def make_dummy_runh(prng, run_number):
    runh = prng.uniform(low=0, high=1, size=273).astype(np.float32)
    runh[cpw.I.RUNH.MARKER] = cpw.I.RUNH.MARKER_FLOAT32
    runh[cpw.I.RUNH.RUN_NUMBER] = np.float32(run_number)
    return runh


def make_dummy_evth(prng, run_number, event_number):
    ehtv = prng.uniform(low=0, high=1, size=273).astype(np.float32)
    ehtv[cpw.I.EVTH.MARKER] = cpw.I.EVTH.MARKER_FLOAT32
    ehtv[cpw.I.EVTH.RUN_NUMBER] = np.float32(run_number)
    ehtv[cpw.I.EVTH.EVENT_NUMBER] = np.float32(event_number)
    return ehtv


def make_dummy_bunches(prng, num_bunches):
    bunches = prng.uniform(low=0, high=1, size=8 * num_bunches).astype(
        np.float32
    )
    bunches = np.reshape(bunches, (num_bunches, 8))
    return bunches


def make_dummy_run(prng, run_number, avg_num_events, avg_num_bunches):
    run = {}
    run["RUNH"] = make_dummy_runh(prng=prng, run_number=run_number)
    run["events"] = {}
    num_events = int(prng.uniform(low=0, high=1, size=avg_num_events)[0])
    num_events = max([num_events, 1])

    for event_number in np.arange(1, num_events + 1):
        event_number = int(event_number)
        num_bunches = int(prng.uniform(low=0, high=1, size=avg_num_bunches)[0])
        run["events"][event_number] = {
            "EVTH": make_dummy_evth(
                prng=prng, run_number=run_number, event_number=event_number
            ),
            "bunches": make_dummy_bunches(prng=prng, num_bunches=num_bunches),
        }
    return run


RUN_NUMBERS = [1, 13, 67, 3877]
AVG_NUM_EVENTS = 25
AVG_NUM_BUNCHES = 10000
SEED = 8443


def test_event_tape_with_contextmanager(debug_dir):
    tmp = cpw.testing.TmpDebugDir(
        debug_dir=debug_dir,
        suffix=inspect.getframeinfo(inspect.currentframe()).function,
    )

    prng = np.random.Generator(np.random.PCG64(SEED))

    for run_number in RUN_NUMBERS:
        orig = make_dummy_run(
            prng=prng,
            run_number=run_number,
            avg_num_events=AVG_NUM_EVENTS,
            avg_num_bunches=AVG_NUM_BUNCHES,
        )
        path = os.path.join(tmp.name, "run{:06d}.evt.tar".format(run_number))

        with cpw.cherenkov.CherenkovEventTapeWriter(
            path=path, buffer_capacity=1000
        ) as ww:
            ww.write_runh(orig["RUNH"])
            for event_number in orig["events"]:
                ww.write_evth(orig["events"][event_number]["EVTH"])
                ww.write_payload(orig["events"][event_number]["bunches"])

        back = {}
        with cpw.cherenkov.CherenkovEventTapeReader(path=path) as rr:
            back["RUNH"] = rr.runh
            back["events"] = {}

            for event in rr:
                evth, bunch_stream = event
                event_number = int(evth[cpw.I.EVTH.EVENT_NUMBER])
                back["events"][event_number] = {"EVTH": evth}
                bunches = []
                for bunch_block in bunch_stream:
                    bunches.append(bunch_block)
                bunches = np.vstack(bunches)
                back["events"][event_number]["bunches"] = bunches

        np.testing.assert_array_equal(orig["RUNH"], back["RUNH"])
        for event_number in orig["events"]:
            evto = orig["events"][event_number]
            evtb = back["events"][event_number]
            np.testing.assert_array_equal(evto["EVTH"], evtb["EVTH"])
            np.testing.assert_array_equal(evto["bunches"], evtb["bunches"])

    tmp.cleanup_when_no_debug()


def test_event_tape_without_contextmanager(debug_dir):
    tmp = cpw.testing.TmpDebugDir(
        debug_dir=debug_dir,
        suffix=inspect.getframeinfo(inspect.currentframe()).function,
    )

    prng = np.random.Generator(np.random.PCG64(SEED))

    for run_number in RUN_NUMBERS:
        orig = make_dummy_run(
            prng=prng,
            run_number=run_number,
            avg_num_events=AVG_NUM_EVENTS,
            avg_num_bunches=AVG_NUM_BUNCHES,
        )
        path = os.path.join(tmp.name, "run{:06d}.evt.tar".format(run_number))

        ww = cpw.cherenkov.CherenkovEventTapeWriter(
            path=path, buffer_capacity=1000
        )
        ww.write_runh(orig["RUNH"])
        for event_number in orig["events"]:
            ww.write_evth(orig["events"][event_number]["EVTH"])
            ww.write_payload(orig["events"][event_number]["bunches"])
        ww.close()
        assert ww.tar.closed

        back = {}
        rr = cpw.cherenkov.CherenkovEventTapeReader(path=path)
        back["RUNH"] = rr.runh
        back["events"] = {}
        for event in rr:
            evth, bunch_stream = event
            event_number = int(evth[cpw.I.EVTH.EVENT_NUMBER])
            back["events"][event_number] = {"EVTH": evth}
            bunches = []
            for bunch_block in bunch_stream:
                bunches.append(bunch_block)
            bunches = np.vstack(bunches)
            back["events"][event_number]["bunches"] = bunches
        rr.close()
        assert rr.tar.closed

        np.testing.assert_array_equal(orig["RUNH"], back["RUNH"])
        for event_number in orig["events"]:
            evto = orig["events"][event_number]
            evtb = back["events"][event_number]
            np.testing.assert_array_equal(evto["EVTH"], evtb["EVTH"])
            np.testing.assert_array_equal(evto["bunches"], evtb["bunches"])

    tmp.cleanup_when_no_debug()
