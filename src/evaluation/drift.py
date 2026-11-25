"""The drift race: wind-twin's design fault grafted onto the healthy turbines.

A +1.5 °C/h rise starts every three days through each test window. Both
residual rules race the static fleet-median rule to detect it within 12 hours.
"""

import numpy as np
import pandas as pd

from src.monitoring.alarms import ABOVE_MEDIAN, MEDIAN_FRAMES, RESIDUAL_FRAMES, RESIDUAL_LIMIT, first_sustained
from src.monitoring.twin import residuals

STEP_RISE, HORIZON, EVERY = 0.25, 72, 432  # 1.5 °C/h at 10 min, 12 h, every 3 days


def race(test, models, fleet_oil, turbine, split):
    rows = []
    segment = np.cumsum(test.new_segment.values)
    for start in range(200, len(test) - HORIZON, EVERY):
        if test.new_segment.values[start:start + HORIZON + 1].any():
            continue
        first = int(np.flatnonzero(segment == segment[start])[0])
        window = slice(first, start + HORIZON)
        length, onset = start + HORIZON - first, start - first
        drift = np.zeros(length)
        drift[onset:] = STEP_RISE * np.arange(1, HORIZON + 1)
        row = dict(split=split, turbine=turbine, start=str(test.t.iloc[start]))
        for name, model in models.items():
            r = residuals(model, test.Gost_avg.values[window], test.Ot_avg.values[window], test.loss.values[window],
                          np.r_[True, np.zeros(length - 1, bool)], drift)
            hit = first_sustained(r[onset:] > RESIDUAL_LIMIT, RESIDUAL_FRAMES)
            row[name] = None if hit is None else (hit + 1) * 10
        times = pd.DatetimeIndex(test.t.iloc[window].iloc[onset:])
        grafted = test.Gost_avg.values[window][onset:] + drift[onset:]
        fleet = np.c_[fleet_oil.reindex(times).drop(columns=turbine).values, grafted]
        hit = first_sustained(grafted > np.nanmedian(fleet, axis=1) + ABOVE_MEDIAN, MEDIAN_FRAMES)
        row["static rule"] = None if hit is None else (hit + 1) * 10
        rows.append(row)
    return rows
