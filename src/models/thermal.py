"""Gearbox oil normal-behaviour model, in two variants that differ only in the steady state.

    unit coupling     T_ss = T_amb + f(loss)             wind-twin, thermal.rs
    fitted coupling   T_ss = a(loss) + k(loss) · T_amb   this study, 0 ≤ k ≤ 1

Loss heat    P_loss = (1 − η) · P / η,  η = 0.97
Dynamics     T[n+1] = T[n] + α · (T_ss − T[n]),  α_heat or α_cool by the sign of the gap,
             each by one-step least squares, as in thermal.rs
"""

import numpy as np

EFFICIENCY = 0.97
BIN_KW = 5.0
BINS = 14
MIN_SAMPLES = 20
MIN_AMBIENT_SPAN = 5.0  # °C of ambient spread a bin needs before its slope is fitted


def loss_kw(power_kw):
    return np.maximum(power_kw, 0.0) / EFFICIENCY * (1.0 - EFFICIENCY)


class GearboxThermalModel:
    def __init__(self, fitted_coupling: bool):
        self.fitted_coupling = fitted_coupling

    def _fit_steady_state(self, temperature, ambient, loss):
        centres, offsets, couplings = [], [], []
        bins = (loss / BIN_KW).astype(int)
        for b in range(BINS):
            inside = bins == b
            if inside.sum() < MIN_SAMPLES:
                continue
            coupling = 1.0
            if self.fitted_coupling and np.ptp(ambient[inside]) > MIN_AMBIENT_SPAN:
                coupling = float(np.clip(np.polyfit(ambient[inside], temperature[inside], 1)[0], 0.0, 1.0))
            centres.append((b + 0.5) * BIN_KW)
            offsets.append(float(np.median(temperature[inside] - coupling * ambient[inside])))
            couplings.append(coupling)
        self.centres, self.offsets, self.couplings = map(np.array, (centres, offsets, couplings))

    def steady_state(self, ambient, loss):
        offset = np.interp(loss, self.centres, self.offsets)
        coupling = np.interp(loss, self.centres, self.couplings)
        return offset + coupling * ambient

    def fit(self, temperature, temperature_next, ambient, loss):
        self._fit_steady_state(temperature, ambient, loss)
        gap = self.steady_state(ambient, loss) - temperature
        step = temperature_next - temperature
        heating = gap >= 0
        self.alpha_heat = float((gap[heating] * step[heating]).sum() / (gap[heating] ** 2).sum())
        self.alpha_cool = float((gap[~heating] * step[~heating]).sum() / (gap[~heating] ** 2).sum())
        return self

    def step(self, modelled, ambient, loss):
        target = self.steady_state(ambient, loss)
        alpha = self.alpha_heat if target >= modelled else self.alpha_cool
        return modelled + alpha * (target - modelled)
