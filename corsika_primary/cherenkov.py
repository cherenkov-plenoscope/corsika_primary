from . import event_tape
import numpy as np


NUM_CHERENKOV_BUNCHES_IN_BUFFER = 1048576


def CherenkovEventTapeWriter(
    path, buffer_capacity=NUM_CHERENKOV_BUNCHES_IN_BUFFER
):
    """
    Write an EventTape. Add RUNH, EVTH, and cherenkov-bunches.

    path : str
        Path to event-tape file.
    buffer_capacity : int
        Buffer-size in cherenkov-bunches.
    """
    return event_tape.EventTapeWriter(
        path=path,
        payload_shape_1=8,
        payload_block_suffix=CHERENKOV_SUFFIX,
        buffer_capacity=buffer_capacity,
    )


def CherenkovEventTapeReader(path):
    return event_tape.EventTapeReader(
        path=path,
        payload_block_suffix=CHERENKOV_SUFFIX,
        func_read_payload_block=read_cherenkov_bunch_block,
    )


CHERENKOV_SUFFIX = ".cer.x8.float32"


def read_cherenkov_bunch_block(tar, tarinfo):
    return event_tape.read_payload_block(tar=tar, tarinfo=tarinfo, shape_1=8)
