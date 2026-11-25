"""The La Haute Borne 2017 SCADA extract, reduced to the columns this study uses.

The source file is about 187 MB with 138 columns. It is streamed once and cut
on the fly to the nine columns needed here, so the full file never lands on
disk. Turbine names follow wind-twin's farm layout.
"""

import csv
import io
import urllib.request
from pathlib import Path

import pandas as pd

URL = ("https://media.githubusercontent.com/media/Loubout/la_haute_borne_data/"
       "main/la-haute-borne-data-2017-2020.csv")
COLUMNS = ["Wind_turbine_name", "Date_time", "P_avg", "Rs_avg",
           "Gost_avg", "Git_avg", "Ot_avg", "Yt_avg", "Ds_avg"]
PATH = Path("data/scada-2017.csv")
TURBINES = {"R80736": "T01", "R80721": "T02", "R80711": "T03", "R80790": "T04"}


def fetch(url: str = URL, path: Path = PATH) -> Path:
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as response, open(path, "w", newline="") as out:
        reader = csv.reader(io.TextIOWrapper(response, encoding="utf-8"), delimiter=";")
        header = next(reader)
        keep = [header.index(column) for column in COLUMNS]
        writer = csv.writer(out)
        writer.writerow(COLUMNS)
        for row in reader:
            writer.writerow([row[i] for i in keep])
    return path


def load() -> pd.DataFrame:
    frame = pd.read_csv(fetch())
    frame["t"] = pd.to_datetime(frame["Date_time"], utc=True)
    frame["turbine"] = frame["Wind_turbine_name"].map(TURBINES)
    frame = frame.drop(columns=["Date_time", "Wind_turbine_name"])
    return frame.sort_values(["turbine", "t"]).reset_index(drop=True)
