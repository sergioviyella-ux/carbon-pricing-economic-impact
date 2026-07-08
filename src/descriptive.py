"""Section 2 "BASIC DESCRIPTIVE ANALYTICS" + "EMISSIONS BY COUNTRY" charts.

Covers: summary()/missing-values checks, top-20 emitters (total + per
capita), average emissions across selected years, and average emissions by
income group.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from . import config as cfg


# ---------------------------------------------------------------------------
# 2. Basic descriptive analytics
# ---------------------------------------------------------------------------


def r_summary(series: pd.Series) -> pd.Series:
    """Replicates R's `summary()` on a numeric vector: Min/1stQu/Median/Mean/3rdQu/Max.

    R's default quantile algorithm (type 7) matches pandas' default
    `Series.quantile()` (linear interpolation), so this lines up exactly.
    """
    s = pd.to_numeric(series, errors="coerce").dropna()
    return pd.Series(
        {
            "Min.": s.min(),
            "1st Qu.": s.quantile(0.25),
            "Median": s.median(),
            "Mean": s.mean(),
            "3rd Qu.": s.quantile(0.75),
            "Max.": s.max(),
        }
    )


def missing_values_table(merged_data: pd.DataFrame) -> pd.Series:
    """R: colSums(is.na(merged_data))"""
    return merged_data.isna().sum()


# ---------------------------------------------------------------------------
# Emissions by country (2023)
# ---------------------------------------------------------------------------


def top_emissions_by_country(merged_data: pd.DataFrame, year: int = 2023, top_n: int = 20) -> pd.DataFrame:
    """R: filter(Year==2023) %>% group_by(Country) %>% summarise(total_emissions=sum(Emissions)) %>% slice_head(20)"""
    return (
        merged_data[merged_data["year"] == year]
        .groupby("country", as_index=False)["emissions"]
        .sum()
        .rename(columns={"emissions": "total_emissions"})
        .sort_values("total_emissions", ascending=False)
        .head(top_n)
    )


def plot_top_emissions_bar(top_emissions: pd.DataFrame, save_path=None):
    """R: geom_bar(fill="steelblue") + coord_flip() + theme(legend.position="none")"""
    plot_df = top_emissions.sort_values("total_emissions", ascending=True)
    fig, ax = plt.subplots(figsize=(9, 8))
    ax.barh(plot_df["country"], plot_df["total_emissions"], color=cfg.COLOR_STEELBLUE)
    ax.set_title("Top 20 Countries with Highest Emissions in 2023")
    ax.set_xlabel("Total Emissions")
    ax.set_ylabel("Country")
    cfg.style_axes(ax)
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150)
    return fig, ax


def top_per_capita_emissions(merged_data: pd.DataFrame, year: int = 2023, top_n: int = 20) -> pd.DataFrame:
    """R: mutate(per_capita_emissions = Emissions/Population) %>% filter(Year==2023, !is.na(...)) %>% arrange(desc()) %>% head(20)"""
    df = merged_data.copy()
    df["per_capita_emissions"] = df["emissions"] / df["population"]
    out = (
        df[(df["year"] == year) & df["per_capita_emissions"].notna()]
        .sort_values("per_capita_emissions", ascending=False)
        .head(top_n)
    )
    return out[["country", "per_capita_emissions"]]


def plot_top_per_capita_emissions(top_per_capita: pd.DataFrame, save_path=None):
    """R: geom_bar(fill="red") + coord_flip()"""
    plot_df = top_per_capita.sort_values("per_capita_emissions", ascending=True)
    fig, ax = plt.subplots(figsize=(9, 8))
    ax.barh(plot_df["country"], plot_df["per_capita_emissions"], color=cfg.COLOR_RED)
    ax.set_title("Top 20 Countries with Highest Emissions Per Capita (2023)")
    ax.set_xlabel("Emissions Per Person (Tons)")
    ax.set_ylabel("Country")
    cfg.style_axes(ax)
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150)
    return fig, ax


# ---------------------------------------------------------------------------
# Average emissions over selected years
# ---------------------------------------------------------------------------

SELECTED_YEARS = [2000, 2010, 2020, 2023]


def average_emissions_selected_years(merged_data: pd.DataFrame) -> pd.DataFrame:
    """R: filter(Year %in% selected_years); stat="summary" fun="mean" per Year"""
    filtered = merged_data[merged_data["year"].isin(SELECTED_YEARS)]
    return filtered.groupby("year", as_index=False)["emissions"].mean().rename(
        columns={"emissions": "mean_emissions"}
    )


def plot_average_emissions_selected_years(avg_by_year: pd.DataFrame, save_path=None):
    """R: geom_bar(stat="summary", fun="mean") with fill=as.factor(Year) -- ggplot's default hue-4 palette."""
    fig, ax = plt.subplots(figsize=(7, 5))
    years = avg_by_year["year"].astype(str).tolist()
    ax.bar(years, avg_by_year["mean_emissions"], color=cfg.GGPLOT_HUE_4[: len(years)])
    ax.set_title("Average Emissions Over Selected Years")
    ax.set_xlabel("Year")
    ax.set_ylabel("Mean Emissions")
    cfg.style_axes(ax)
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150)
    return fig, ax


# ---------------------------------------------------------------------------
# Average emissions by income group
# ---------------------------------------------------------------------------


def classify_income_group(merged_data: pd.DataFrame) -> pd.DataFrame:
    """R: case_when(gdp_per_capita >= 40000 ~ "High Income", >= 15000 ~ "Upper Middle Income",
    >= 5000 ~ "Lower Middle Income", TRUE ~ "Low Income")
    """
    df = merged_data.copy()
    conditions = [
        df["gdp_per_capita"] >= 40000,
        df["gdp_per_capita"] >= 15000,
        df["gdp_per_capita"] >= 5000,
    ]
    choices = ["High Income", "Upper Middle Income", "Lower Middle Income"]
    df["income_group"] = np.select(conditions, choices, default="Low Income")
    # case_when's implicit NA propagation: unknown GDP per capita -> unknown group
    df.loc[df["gdp_per_capita"].isna(), "income_group"] = np.nan
    return df


INCOME_GROUP_ORDER = ["Low Income", "Lower Middle Income", "Upper Middle Income", "High Income"]


def average_emissions_by_income_group(merged_data: pd.DataFrame) -> pd.DataFrame:
    """R: stat_summary(fun=mean, geom="line") by Year, colored by income_group"""
    df = classify_income_group(merged_data)
    return (
        df.dropna(subset=["income_group"])
        .groupby(["year", "income_group"], as_index=False)["emissions"]
        .mean()
        .rename(columns={"emissions": "mean_emissions"})
    )


def plot_average_emissions_by_income_group(by_group: pd.DataFrame, save_path=None):
    fig, ax = plt.subplots(figsize=(9, 5.5))
    for color, group in zip(cfg.GGPLOT_HUE_4, INCOME_GROUP_ORDER):
        sub = by_group[by_group["income_group"] == group].sort_values("year")
        if sub.empty:
            continue
        ax.plot(sub["year"], sub["mean_emissions"], color=color, linewidth=1.5, label=group)
    ax.set_title("Average Emissions by Income Group")
    ax.set_xlabel("Year")
    ax.set_ylabel("Emissions")
    cfg.style_axes(ax)
    ax.legend(title="Income Group", loc="upper left", bbox_to_anchor=(1.0, 1.0))
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig, ax
