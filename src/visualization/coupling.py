"""Ambient coupling by load: what the archive shows against what the model assumed."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from src.visualization import style


def draw(theme: str, directory: Path) -> None:
    colors = style.apply(theme)
    data = pd.read_csv("results/ambient-coupling.csv")
    figure, axis = plt.subplots(figsize=(11, 3.6))
    axis.set_xlim(0, 70)
    axis.set_ylim(0, 1.12)
    axis.axhline(1.0, color=colors["ink"], linewidth=1.0, linestyle=(0, (4, 3)))
    figure.canvas.draw()
    style.rounded_bars(axis, data.loss_kw, data.coupling, [colors["base"]] * len(data), width=3.4, radius=0.9)
    axis.set_title("Ambient Coupling")
    axis.set_xlabel("Drivetrain loss, kW")
    axis.set_ylabel("°C of oil per °C of ambient")
    style.legend(figure, [(colors["base"], "Measured"), (colors["ink"], "Assumed by the model")], colors)
    figure.tight_layout()
    style.save(figure, directory, "coupling", theme)


if __name__ == "__main__":
    for theme in ("light", "dark"):
        draw(theme, Path("docs/images"))
