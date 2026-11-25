"""Alarm rules as defined in wind-twin.

    THERMAL_RESIDUAL_HIGH   residual > 4 °C for 6 frames             twin-physics/enrich.rs
    GEARBOX_TEMP_HIGH       oil > fleet median + 5 °C for 3 frames   twin-ingest/alarms.rs
"""

RESIDUAL_LIMIT, RESIDUAL_FRAMES = 4.0, 6
ABOVE_MEDIAN, MEDIAN_FRAMES = 5.0, 3


def first_sustained(flags, frames):
    """Index at which the flag has held for the given number of frames, or None."""
    run = 0
    for i, flag in enumerate(flags):
        run = run + 1 if flag else 0
        if run >= frames:
            return i
    return None


def episodes(flags, frames):
    """Number of separate alarms raised."""
    run, count = 0, 0
    for flag in flags:
        run = run + 1 if flag else 0
        count += run == frames
    return count
