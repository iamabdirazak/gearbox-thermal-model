"""False alarms on healthy turbines and time to detect the grafted drift."""

import json
from pathlib import Path

import matplotlib.pyplot as plt

from src.visualization import style


def draw(theme: str, directory: Path) -> None:
    colors = style.apply(theme)
    summary = json.loads(Path("results/summary.json").read_text())
    unit, fitted, rule = summary["unit coupling"], summary["fitted coupling"], summary["static rule"]
    panels = [
        ("False Alarms", "Per turbine-month", "{:.1f}",
         [("Unit coupling", unit["false_alarms_per_turbine_month"], colors["soft"]),
          ("Fitted coupling", fitted["false_alarms_per_turbine_month"], colors["base"])]),
        ("Time to Detect", "Median minutes", "{:.0f}",
         [("Unit coupling", unit["median_minutes_to_detect"], colors["soft"]),
          ("Static rule", rule["median_minutes_to_detect"], colors["secondary"]),
          ("Fitted coupling", fitted["median_minutes_to_detect"], colors["base"])]),
    ]
    figure, axes = plt.subplots(1, 2, figsize=(11, 3.6))
    for axis, (title, label, fmt, bars) in zip(axes, panels):
        top = max(value for _, value, _ in bars) * 1.18
        axis.set_xlim(-0.6, len(bars) - 0.4)
        axis.set_ylim(0, top)
        figure.canvas.draw()
        style.rounded_bars(axis, range(len(bars)), [v for _, v, _ in bars], [c for _, _, c in bars], width=0.5, radius=0.06)
        for i, (_, value, _) in enumerate(bars):
            axis.text(i, value + top * 0.025, fmt.format(value), ha="center", fontsize=9, fontweight="semibold",
                      color=colors["ink"])
        axis.set_xticks(range(len(bars)), [name for name, _, _ in bars])
        axis.set_title(title)
        axis.set_ylabel(label)
    figure.tight_layout(w_pad=3)
    style.save(figure, directory, "drift", theme)


if __name__ == "__main__":
    for theme in ("light", "dark"):
        draw(theme, Path("docs/images"))
