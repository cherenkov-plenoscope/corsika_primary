from .. import event_tape


def ParticleEventTapeWriter(path, buffer_capacity=1000 * 1000):
    """
    Write a ParticleEventTape. Add RUNH, EVTH, and particles.

    path : str
        Path to event-tape file.
    buffer_capacity : int
        Buffer-size in num. particles.
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
