"""Carbon tax / ETS trend, heatmap, adoption, volatility, distribution, and
top-taxed-country sections of the R draft (headers: "TENDENCY OVER TIME",
"Heatmap...", "Adoption of carbon prices", "Tax volatility",
"DISTRIBUTIONS...", "Carbon price distribution", "Top Countries...").
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

from . import config as cfg

SELECTED_YEARS = [2000, 2010, 2020, 2023]

# ggplot2's scale_fill_gradient(low="white", high=<color>)
CMAP_WHITE_TO_BLUE = LinearSegmentedColormap.from_list("white_to_blue", ["white", "blue"])
CMAP_WHITE_TO_RED = LinearSegmentedColormap.from_list("white_to_red", ["white", "red"])


# ---------------------------------------------------------------------------
# Tendency over time
# ---------------------------------------------------------------------------


def carbon_tax_trend(merged_data: pd.DataFrame) -> pd.DataFrame:
    return (
        merged_data.groupby("year", as_index=False)["average_carbon_tax"]
        .mean()
        .rename(columns={"average_carbon_tax": "mean_carbon_tax"})
    )


def ets_trend(merged_data: pd.DataFrame) -> pd.DataFrame:
    return (
        merged_data.groupby("year", as_index=False)["average_ets"]
        .mean()
        .rename(columns={"average_ets": "mean_ets"})
    )


def _plot_line_point(x, y, color, title, ylabel, save_path=None):
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(x, y, color=color, linewidth=1.5, zorder=2)
    ax.scatter(x, y, color=color, s=30, zorder=3)
    ax.set_title(title)
    ax.set_xlabel("Year")
    ax.set_ylabel(ylabel)
    cfg.style_axes(ax)
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150)
    return fig, ax


def plot_carbon_tax_trend(trend: pd.DataFrame, save_path=None):
    return _plot_line_point(
        trend["year"], trend["mean_carbon_tax"], cfg.COLOR_BLUE,
        "Carbon Tax Evolution Over Time", "Average Carbon Tax", save_path,
    )


def plot_ets_trend(trend: pd.DataFrame, save_path=None):
    return _plot_line_point(
        trend["year"], trend["mean_ets"], cfg.COLOR_RED,
        "ETS Evolution Over Time", "Average ETS Price", save_path,
    )


# ---------------------------------------------------------------------------
# Heatmaps: carbon tax / ETS by year, for countries that ever had either
# ---------------------------------------------------------------------------


def relevant_countries(merged_data: pd.DataFrame) -> list:
    mask = ((merged_data["average_carbon_tax"].notna()) & (merged_data["average_carbon_tax"] > 0)) | (
        (merged_data["average_ets"].notna()) & (merged_data["average_ets"] > 0)
    )
    return sorted(merged_data.loc[mask, "country"].unique())


def _plot_heatmap(merged_data: pd.DataFrame, value_col: str, cmap, title, cbar_label, save_path=None):
    countries = relevant_countries(merged_data)
    filtered = merged_data[merged_data["country"].isin(countries)]
    pivot = filtered.pivot_table(index="country", columns="year", values=value_col, aggfunc="mean")
    pivot = pivot.reindex(sorted(pivot.index, reverse=True))

    fig, ax = plt.subplots(figsize=(12, 10))
    im = ax.pcolormesh(pivot.columns, np.arange(len(pivot.index)), pivot.values, cmap=cmap, shading="nearest")
    ax.set_yticks(np.arange(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    ax.set_title(title)
    ax.set_xlabel("Year")
    ax.set_ylabel("Country")
    cfg.style_axes(ax)
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label(cbar_label)
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150)
    return fig, ax


def plot_carbon_tax_heatmap(merged_data: pd.DataFrame, save_path=None):
    return _plot_heatmap(
        merged_data, "average_carbon_tax", CMAP_WHITE_TO_BLUE,
        "Heatmap of Carbon Tax by Year (Selected Countries)", "Carbon Tax", save_path,
    )


def plot_ets_heatmap(merged_data: pd.DataFrame, save_path=None):
    return _plot_heatmap(
        merged_data, "average_ets", CMAP_WHITE_TO_RED,
        "Heatmap of ETS by Year (Selected Countries)", "ETS Price", save_path,
    )


# ---------------------------------------------------------------------------
# Policy start (first year of carbon tax or ETS implementation)
# ---------------------------------------------------------------------------


def policy_start_years(merged_data: pd.DataFrame) -> pd.DataFrame:
    mask = (merged_data["average_carbon_tax"] > 0) | (merged_data["average_ets"] > 0)
    return (
        merged_data[mask]
        .groupby("country", as_index=False)["year"]
        .min()
        .rename(columns={"year": "first_year"})
        .sort_values("first_year")
    )


def plot_policy_start(policy_start: pd.DataFrame, save_path=None):
    plot_df = policy_start.sort_values("first_year", ascending=False)
    fig, ax = plt.subplots(figsize=(9, 8))
    ax.barh(plot_df["country"], plot_df["first_year"], color=cfg.COLOR_BLUE)
    ax.set_title("First Year of Carbon Tax or ETS Implementation")
    ax.set_xlabel("First Year")
    ax.set_ylabel("Country")
    cfg.style_axes(ax)
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150)
    return fig, ax


# ---------------------------------------------------------------------------
# Adoption of carbon prices over time
# ---------------------------------------------------------------------------


def carbon_tax_adoption(merged_data: pd.DataFrame) -> pd.DataFrame:
    mask = merged_data["average_carbon_tax"].notna() & (merged_data["average_carbon_tax"] > 0)
    return (
        merged_data[mask]
        .groupby("year", as_index=False)["country"]
        .nunique()
        .rename(columns={"country": "countries_with_carbon_tax"})
    )


def ets_adoption(merged_data: pd.DataFrame) -> pd.DataFrame:
    mask = merged_data["average_ets"].notna() & (merged_data["average_ets"] > 0)
    return (
        merged_data[mask]
        .groupby("year", as_index=False)["country"]
        .nunique()
        .rename(columns={"country": "countries_with_ets"})
    )


def plot_carbon_tax_adoption(adoption: pd.DataFrame, save_path=None):
    return _plot_line_point(
        adoption["year"], adoption["countries_with_carbon_tax"], cfg.COLOR_BLUE,
        "Number of Countries Adopting Carbon Tax Over Time", "Number of Countries", save_path,
    )


def plot_ets_adoption(adoption: pd.DataFrame, save_path=None):
    return _plot_line_point(
        adoption["year"], adoption["countries_with_ets"], cfg.COLOR_RED,
        "Number of Countries Adopting ETS Over Time", "Number of Countries", save_path,
    )


# ---------------------------------------------------------------------------
# Tax volatility (year-over-year absolute change, per country)
# ---------------------------------------------------------------------------


def compute_volatility(merged_data: pd.DataFrame) -> pd.DataFrame:
    """R: arrange(Country,Year) %>% group_by(Country) %>%
    mutate(carbon_tax_volatility = abs(x - lag(x)), ets_volatility = abs(y - lag(y)))
    """
    df = merged_data.sort_values(["country", "year"]).copy()
    df["carbon_tax_volatility"] = df.groupby("country")["average_carbon_tax"].diff().abs()
    df["ets_volatility"] = df.groupby("country")["average_ets"].diff().abs()
    return df


def _plot_volatility_spaghetti(df: pd.DataFrame, value_col: str, title, ylabel, save_path=None):
    """229 countries make a legend impractical (as it would in ggplot too) --
    lines are colored by country via a cycling colormap, legend omitted.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    countries = df["country"].unique()
    colors = plt.cm.hsv(np.linspace(0, 1, len(countries), endpoint=False))
    for country, color in zip(countries, colors):
        sub = df[(df["country"] == country) & df[value_col].notna()]
        if sub.empty:
            continue
        ax.plot(sub["year"], sub[value_col], color=color, linewidth=0.8, alpha=0.7)
    ax.set_title(title)
    ax.set_xlabel("Year")
    ax.set_ylabel(ylabel)
    cfg.style_axes(ax)
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150)
    return fig, ax


def plot_carbon_tax_volatility(df: pd.DataFrame, save_path=None):
    return _plot_volatility_spaghetti(
        df, "carbon_tax_volatility", "Carbon Tax Volatility Over Time",
        "Yearly Change in Carbon Tax", save_path,
    )


def plot_ets_volatility(df: pd.DataFrame, save_path=None):
    return _plot_volatility_spaghetti(
        df, "ets_volatility", "ETS Volatility Over Time",
        "Yearly Change in ETS Price", save_path,
    )


# ---------------------------------------------------------------------------
# Distributions: histograms & boxplots
# ---------------------------------------------------------------------------


def plot_histograms(merged_data: pd.DataFrame, save_path=None):
    """R: par(mfrow=c(1,2)); hist(...)"""
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    axes[0].hist(merged_data["average_carbon_tax"].dropna(), color=cfg.COLOR_BLUE)
    axes[0].set_title("Histogram of Carbon Tax")
    axes[0].set_xlabel("Carbon Tax")
    axes[0].set_ylabel("Frequency")
    axes[1].hist(merged_data["average_ets"].dropna(), color=cfg.COLOR_RED)
    axes[1].set_title("Histogram of ETS")
    axes[1].set_xlabel("ETS")
    axes[1].set_ylabel("Frequency")
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150)
    return fig, axes


def plot_boxplots_overall(merged_data: pd.DataFrame, save_path=None):
    """R: par(mfrow=c(1,2)); boxplot(...)"""
    fig, axes = plt.subplots(1, 2, figsize=(8, 5))
    axes[0].boxplot(
        merged_data["average_carbon_tax"].dropna(), patch_artist=True,
        boxprops=dict(facecolor=cfg.COLOR_BLUE), medianprops=dict(color="black"),
    )
    axes[0].set_title("Boxplot of Carbon Tax")
    axes[0].set_xticks([])
    axes[1].boxplot(
        merged_data["average_ets"].dropna(), patch_artist=True,
        boxprops=dict(facecolor=cfg.COLOR_RED), medianprops=dict(color="black"),
    )
    axes[1].set_title("Boxplot of ETS")
    axes[1].set_xticks([])
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150)
    return fig, axes


def _plot_boxplot_by_year(merged_data: pd.DataFrame, value_col, color, title, ylabel, save_path=None):
    filtered = merged_data[merged_data["year"].isin(SELECTED_YEARS)]
    data = [filtered.loc[filtered["year"] == y, value_col].dropna() for y in SELECTED_YEARS]
    fig, ax = plt.subplots(figsize=(7, 5))
    bp = ax.boxplot(data, tick_labels=[str(y) for y in SELECTED_YEARS], patch_artist=True)
    for box in bp["boxes"]:
        box.set_facecolor(color)
        box.set_alpha(0.7)
    ax.set_title(title)
    ax.set_xlabel("Year")
    ax.set_ylabel(ylabel)
    cfg.style_axes(ax)
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150)
    return fig, ax


def plot_carbon_tax_boxplot_by_year(merged_data: pd.DataFrame, save_path=None):
    return _plot_boxplot_by_year(
        merged_data, "average_carbon_tax", cfg.COLOR_STEELBLUE,
        "Distribution of Carbon Tax Over Selected Years", "Carbon Tax", save_path,
    )


def plot_ets_boxplot_by_year(merged_data: pd.DataFrame, save_path=None):
    return _plot_boxplot_by_year(
        merged_data, "average_ets", cfg.COLOR_RED,
        "Distribution of ETS Over Selected Years", "ETS Price", save_path,
    )


# ---------------------------------------------------------------------------
# Top countries with highest carbon taxes/ETS (2024)
# ---------------------------------------------------------------------------


def top_taxed_countries(merged_data: pd.DataFrame, year: int = 2024, top_n: int = 10) -> pd.DataFrame:
    mask = (merged_data["year"] == year) & merged_data["average_carbon_tax"].notna() & (
        merged_data["average_carbon_tax"] > 0
    )
    return merged_data.loc[mask, ["country", "average_carbon_tax"]].sort_values(
        "average_carbon_tax", ascending=False
    ).head(top_n)


def top_ets_countries(merged_data: pd.DataFrame, year: int = 2024, top_n: int = 10) -> pd.DataFrame:
    mask = (merged_data["year"] == year) & merged_data["average_ets"].notna() & (merged_data["average_ets"] > 0)
    return merged_data.loc[mask, ["country", "average_ets"]].sort_values(
        "average_ets", ascending=False
    ).head(top_n)


def plot_top_taxed(top_taxed: pd.DataFrame, save_path=None):
    plot_df = top_taxed.sort_values("average_carbon_tax", ascending=True)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(plot_df["country"], plot_df["average_carbon_tax"], color=cfg.COLOR_BLUE)
    ax.set_title("Top 10 Countries with Highest Carbon Tax in 2024")
    ax.set_xlabel("Carbon Tax")
    ax.set_ylabel("Country")
    cfg.style_axes(ax)
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150)
    return fig, ax


def plot_top_ets(top_ets: pd.DataFrame, save_path=None):
    plot_df = top_ets.sort_values("average_ets", ascending=True)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(plot_df["country"], plot_df["average_ets"], color=cfg.COLOR_RED)
    ax.set_title("Top 10 Countries with Highest ETS in 2024")
    ax.set_xlabel("ETS Price")
    ax.set_ylabel("Country")
    cfg.style_axes(ax)
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150)
    return fig, ax
