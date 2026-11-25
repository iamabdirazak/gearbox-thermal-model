"""What every evaluation shares: the seasonal splits, the models and the running data.

Each model is fitted on one season and tested on the rest of 2017. Only
running periods count, and a gap in the 10-minute record starts a new segment.
"""

from src.models.thermal import loss_kw

SPLITS = {
    "fit Apr-Jun, test Jul-Dec": (("2017-04-01", "2017-07-01"), ("2017-07-01", "2018-01-01")),
    "fit Oct-Dec, test Jan-Sep": (("2017-10-01", "2018-01-01"), ("2017-01-01", "2017-10-01")),
}
MODELS = {"unit coupling": False, "fitted coupling": True}
HEALTHY = ["T01", "T02", "T04"]


def running(frame):
    frame = frame[frame.P_avg > 0].dropna(subset=["Gost_avg", "Ot_avg"]).copy()
    frame["loss"] = loss_kw(frame.P_avg.values)
    frame["new_segment"] = frame.t.diff().dt.total_seconds().ne(600).values
    return frame.reset_index(drop=True)


def training_pairs(frame):
    following = frame.shift(-1)
    usable = ~following.new_segment.astype("boolean").fillna(True).to_numpy(bool)
    return (frame.Gost_avg.values[usable], following.Gost_avg.values[usable],
            frame.Ot_avg.values[usable], frame.loss.values[usable])


def windows(frame, split):
    (fit_start, fit_end), (test_start, test_end) = split
    fit = frame[(frame.t >= fit_start) & (frame.t < fit_end)].reset_index(drop=True)
    test = frame[(frame.t >= test_start) & (frame.t < test_end)].reset_index(drop=True)
    test.loc[0, "new_segment"] = True
    return fit, test
