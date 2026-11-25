"""Open-loop deployment with slow bias adaptation, as in thermal.rs ThermalState::advance.

The residual is measured before adaptation, so every expected value is an
honest prediction from past data. Segments restart from the measurement after
any gap.
"""

import numpy as np

ADAPTATION = 0.03  # per 10-minute interval, about 5.5 h tracking time


def residuals(model, temperature, ambient, loss, new_segment, drift=None):
    measured = temperature if drift is None else temperature + drift
    out = np.full(len(temperature), np.nan)
    state = measured[0]
    for i in range(len(temperature)):
        if new_segment[i]:
            state = measured[i]
            continue
        expected = model.step(state, ambient[i], loss[i])
        out[i] = measured[i] - expected
        state = expected + ADAPTATION * (measured[i] - expected)
    return out
