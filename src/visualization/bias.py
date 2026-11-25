"""Seasonal bias: monthly out-of-sample residual per turbine, with each coupling."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from src.visualization import style

MONTHS = list("JFMAMJJASOND")


def draw(theme: str, directory: Path) -> None:
    colors = style.apply(theme)
    data = pd.read_csv("results/monthly-residual.csv")
    unseen = ((data.split.str.startswith("fit Oct")) & (data.month <= 9)) | \
             ((data.split.str.startswith("fit Apr")) & (data.month >= 10))
    data = data[unseen]
    figure, axes = plt.subplots(1, 2, figsize=(11, 3.8), sharey=True)
    for axis, model, title in ((axes[0], "unit coupling", "Unit Coupling"),
                               (axes[1], "fitted coupling", "Fitted Coupling")):
        for turbine in ("T01", "T02", "T04", "T03"):
            series = data[(data.model == model) & (data.turbine == turbine)].sort_values("month")
            hot = turbine == "T03"
            axis.plot(series.month, series.residual_c, linewidth=1.3 if hot else 1.8,
                      color=colors["secondary"] if hot else colors["base"],
                      linestyle=(0, (3, 2)) if hot else "-", marker="o", markersize=2.8)
            if hot:
                axis.annotate("T03", (12, series.residual_c.iloc[-1]), xytext=(6, 0), textcoords="offset points",
                              va="center", fontsize=8, color=colors["secondary"])
        axis.axhline(0, color=colors["hairline"], linewidth=0.8)
        axis.set_xticks(range(1, 13), MONTHS)
        axis.set_xlim(0.5, 12.9)
        axis.set_title(title)
    axes[0].set_ylabel("Monthly median residual, °C")
    style.legend(figure, [(colors["base"], "Healthy turbines"), (colors["secondary"], "T03")], colors)
    figure.tight_layout(w_pad=2.5)
    style.save(figure, directory, "bias", theme)


if __name__ == "__main__":
    for theme in ("light", "dark"):
        draw(theme, Path("docs/images"))
