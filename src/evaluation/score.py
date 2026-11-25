"""Run the whole comparison and write results/.

1. The ambient coupling measured from the archive.
2. Out-of-sample residuals for both models, in two seasonal splits.
3. The drift race on the healthy turbines.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.data.archive import load
from src.evaluation import coupling, drift
from src.evaluation.splits import HEALTHY, MODELS, SPLITS, running, training_pairs, windows
from src.models.thermal import GearboxThermalModel
from src.monitoring.alarms import RESIDUAL_FRAMES, RESIDUAL_LIMIT, episodes
from src.monitoring.twin import residuals

RESULTS = Path("results")


def main():
    RESULTS.mkdir(exist_ok=True)
    frame = load()
    fleet_oil = frame.pivot_table(index="t", columns="turbine", values="Gost_avg")
    coupling.measure(frame).to_csv(RESULTS / "ambient-coupling.csv", index=False)

    residual_rows, constant_rows, monthly_rows, race_rows = [], [], [], []
    for split, bounds in SPLITS.items():
        for turbine, group in frame.groupby("turbine"):
            fit, test = windows(running(group), bounds)
            models = {name: GearboxThermalModel(fitted).fit(*training_pairs(fit)) for name, fitted in MODELS.items()}
            months = (test.t.max() - test.t.min()).days / 30.4
            for name, model in models.items():
                r = residuals(model, test.Gost_avg.values, test.Ot_avg.values, test.loss.values, test.new_segment.values)
                valid = r[~np.isnan(r)]
                residual_rows.append(dict(
                    split=split, turbine=turbine, model=name, std_c=valid.std(),
                    median_abs_c=np.median(np.abs(valid)), p99_abs_c=np.percentile(np.abs(valid), 99),
                    false_alarms_per_month=episodes(r > RESIDUAL_LIMIT, RESIDUAL_FRAMES) / months))
                constant_rows.append(dict(split=split, turbine=turbine, model=name, alpha_heat=model.alpha_heat,
                                          alpha_cool=model.alpha_cool, ratio=model.alpha_heat / model.alpha_cool))
                for month, value in pd.Series(r).groupby(test.t.dt.month.values).median().items():
                    monthly_rows.append(dict(split=split, turbine=turbine, model=name, month=int(month), residual_c=value))
            if turbine in HEALTHY:
                race_rows += drift.race(test, models, fleet_oil, turbine, split)

    result, constants, race = pd.DataFrame(residual_rows), pd.DataFrame(constant_rows), pd.DataFrame(race_rows)
    result.to_csv(RESULTS / "residuals.csv", index=False)
    constants.to_csv(RESULTS / "time-constants.csv", index=False)
    pd.DataFrame(monthly_rows).to_csv(RESULTS / "monthly-residual.csv", index=False)
    race.to_csv(RESULTS / "drift-race.csv", index=False)

    summary = {"grafts": len(race)}
    healthy = result[result.turbine.isin(HEALTHY)]
    for name in MODELS:
        h = healthy[healthy.model == name]
        both = race.dropna(subset=[name, "static rule"])
        summary[name] = dict(
            residual_std_c=round(h.std_c.mean(), 2),
            p99_abs_residual_c=round(h.p99_abs_c.mean(), 2),
            false_alarms_per_turbine_month=round(h.false_alarms_per_month.mean(), 2),
            heat_cool_ratio=round(constants[(constants.model == name) & constants.turbine.isin(HEALTHY)].ratio.mean(), 2),
            detected_pct=round(race[name].notna().mean() * 100, 1),
            median_minutes_to_detect=float(race[name].median()),
            beats_static_rule_pct=round((both[name] < both["static rule"]).mean() * 100, 1),
            median_lead_vs_static_min=float((both["static rule"] - both[name]).median()))
    summary["static rule"] = dict(detected_pct=round(race["static rule"].notna().mean() * 100, 1),
                                  median_minutes_to_detect=float(race["static rule"].median()))
    (RESULTS / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
