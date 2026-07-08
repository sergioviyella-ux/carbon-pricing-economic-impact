"""Second "TRENDS" section: carbon tax vs economic indicators.

Covers the scatter-plot loop (log-transform + inflation y-cap special
cases), the listwise-deletion correlation matrix, and the renewable-energy
jitter plot with a log10 y-scale.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from . import config as cfg

SCATTER_VARS = ["gdp", "gdp_per_capita", "inflation", "unemployment", "exports", "imports"]
LOG_TRANSFORM_VARS = ["gdp", "gdp_per_capita", "exports", "imports"]

CORRELATION_VARS = ["average_carbon_tax", "average_ets", "gdp", "gdp_per_capita", "inflation", "unemployment"]


def plot_carbon_tax_scatter(merged_data: pd.DataFrame, var: str, save_path=None):
    """R: geom_point(alpha=0.5, color="blue") + geom_smooth(method="lm", se=FALSE, color="red")
    Log-transforms gdp/gdp_per_capita/exports/imports; caps y to [0,20] for inflation
    (via coord_cartesian, which crops the view without refitting the lm line).
    """
    label = cfg.VARIABLE_LABELS[var]
    df = merged_data[["average_carbon_tax", var]].dropna()
    x = df["average_carbon_tax"].to_numpy()

    if var in LOG_TRANSFORM_VARS:
        y = np.log(df[var].to_numpy())
        ylabel = f"Log of {label}"
    else:
        y = df[var].to_numpy()
        ylabel = label

    slope, intercept = np.polyfit(x, y, 1)
    xs = np.linspace(x.min(), x.max(), 100)

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(x, y, color=cfg.COLOR_BLUE, alpha=0.5, s=20)
    ax.plot(xs, slope * xs + intercept, color=cfg.COLOR_RED, linewidth=1.5)
    if var == "inflation":
        ax.set_ylim(0, 20)
    ax.set_title(f"Carbon Tax vs {label}")
    ax.set_xlabel("Average Carbon Tax")
    ax.set_ylabel(ylabel)
    cfg.style_axes(ax)
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150)
    return fig, ax


def correlation_matrix(merged_data: pd.DataFrame) -> pd.DataFrame:
    """R: cor(..., use="complete.obs") -- listwise deletion across ALL selected columns
    (not pandas' default pairwise deletion), so rows are dropped first.
    """
    sub = merged_data[CORRELATION_VARS].apply(pd.to_numeric, errors="coerce").dropna()
    return sub.corr()


def plot_renewable_vs_carbon_tax(merged_data: pd.DataFrame, seed: int = 42, save_path=None):
    """R: geom_jitter(color="green", alpha=0.3, width=0.2, height=0.2) +
    geom_smooth(method="lm", se=FALSE, color="black") + scale_y_log10()

    `scale_y_log10()` transforms the data before stats are computed, so the lm
    fit runs on log10(renewable_energy_pct) ~ average_carbon_tax and is then
    back-transformed for display; jitter is a display-only offset applied to
    the scatter points, not to the values the trend line is fit on.
    """
    df = merged_data[["average_carbon_tax", "renewable_energy_pct"]].dropna()
    df = df[df["renewable_energy_pct"] > 0]

    x = df["average_carbon_tax"].to_numpy()
    y = df["renewable_energy_pct"].to_numpy()
    slope, intercept = np.polyfit(x, np.log10(y), 1)

    rng = np.random.default_rng(seed)
    x_jit = x + rng.uniform(-0.2, 0.2, len(x))
    y_jit = np.clip(y + rng.uniform(-0.2, 0.2, len(y)), 1e-3, None)

    xs = np.linspace(x.min(), x.max(), 100)
    fitted = 10 ** (slope * xs + intercept)

    fig, ax = plt.subplots(figsize=(7.5, 5.5))
    ax.scatter(x_jit, y_jit, color=cfg.COLOR_GREEN, alpha=0.3, s=20)
    ax.plot(xs, fitted, color=cfg.COLOR_BLACK, linewidth=1.5)
    ax.set_yscale("log")
    ax.set_title("Carbon Tax vs Renewable Energy Consumption")
    ax.set_xlabel("Average Carbon Tax")
    ax.set_ylabel("Renewable Energy Consumption (% of Total Final Energy)")
    cfg.style_axes(ax)
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150)
    return fig, ax
