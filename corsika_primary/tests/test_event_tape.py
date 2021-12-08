import pytest
from corsika_primary import event_tape as evtar
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
    runh = prng.uniform(size=273).astype(np.float32)
    runh[cpw.I.RUNH.MARKER] = cpw.I.RUNH.MARKER_FLOAT32
    runh[cpw.I.RUNH.RUN_NUMBER] = np.float32(run_number)
    return runh


def make_dummy_evth(prng, run_number, event_number):
    ehtv = prng.uniform(size=273).astype(np.float32)
    ehtv[cpw.I.EVTH.MARKER] = cpw.I.EVTH.MARKER_FLOAT32
    ehtv[cpw.I.EVTH.RUN_NUMBER] = np.float32(run_number)
    ehtv[cpw.I.EVTH.EVENT_NUMBER] = np.float32(event_number)
    return ehtv


def make_dummy_bunches(prng, num_bunches):
    bunches = prng.uniform(size=8*num_bunches).astype(np.float32)
    bunches = np.reshape(bunches, (num_bunches, 8))
    return bunches


def make_dummy_run(prng, run_number, avg_num_events, avg_num_bunches):
    run = {}
    run["RUNH"] = make_dummy_runh(prng=prng, run_number=run_number)
    run["events"] = {}
    num_events = int(prng.uniform(avg_num_events))
    num_events = max([num_events, 1])

    for event_number in np.arange(1, num_events + 1):
        event_number = int(event_number)
        num_bunches = int(prng.uniform(avg_num_bunches))
        run["events"][event_number] = {
            "EVTH": make_dummy_evth(
                prng=prng,
                run_number=run_number,
                event_number=event_number
            ),
            "bunches":  make_dummy_bunches(
                prng=prng,
                num_bunches=num_bunches
            ),
        }
    return run


def test_event_tape(debug_dir):
    tmp = cpw.testing.TmpDebugDir(
        debug_dir=debug_dir,
        suffix=inspect.getframeinfo(inspect.currentframe()).function,
    )

    prng = np.random.Generator(np.random.PCG64(8443))

    for run_number in [1, 13, 67, 3877]:

        run_orig = make_dummy_run(
            prng=prng,
            run_number=run_number,
            avg_num_events=25,
            avg_num_bunches=10000
        )
        path = os.path.join(tmp.name, "run{:06d}.evt.tar".format(run_number))

        with evtar.EventTapeWriter(path=path, buffer_capacity=1000) as ww:
            ww.write_runh(run_orig["RUNH"])
            for event_number in run_orig["events"]:
                ww.write_evth(run_orig["events"][event_number]["EVTH"])
                ww.write_bunches(run_orig["events"][event_number]["bunches"])

        run_back = {}
        with evtar.EventTapeReader(path=path, read_block_by_block=True) as rr:
            run_back["RUNH"] = rr.runh
            run_back["events"] = {}

            for event in rr:
                evth, bunch_stream = event
                event_number = int(evth[cpw.I.EVTH.EVENT_NUMBER])
                run_back["events"][event_number] = {"EVTH": evth}
                bunches = []
                for bunch_block in bunch_stream:
                    bunches.append(bunch_block)
                bunches = np.vstack(bunches)
                run_back["events"][event_number]["bunches"] = bunches

        np.testing.assert_array_equal(run_orig["RUNH"], run_back["RUNH"])
        for event_number in run_orig["events"]:
            evto = run_orig["events"][event_number]
            evtb = run_back["events"][event_number]
            np.testing.assert_array_equal(evto["EVTH"], evtb["EVTH"])
            np.testing.assert_array_equal(evto["bunches"], evtb["bunches"])

    tmp.cleanup_when_no_debug()
