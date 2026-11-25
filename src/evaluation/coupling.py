"""The ambient coupling measured straight from the archive, per 5 kW load bin."""

import numpy as np
import pandas as pd

from src.evaluation.splits import running


def measure(frame) -> pd.DataFrame:
    data = running(frame)
    rows = []
    for b in range(14):
        inside = (data.loss >= b * 5) & (data.loss < (b + 1) * 5)
        if inside.sum() > 200:
            slope = np.polyfit(data.Ot_avg[inside], data.Gost_avg[inside], 1)[0]
            rows.append(dict(loss_kw=b * 5 + 2.5, coupling=round(float(slope), 3), samples=int(inside.sum())))
    return pd.DataFrame(rows)
