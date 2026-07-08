"""Section 3 "DID ANALYSIS": difference-in-differences on 16 early/late
carbon-pricing adopters vs. 8 never-adopters.

Estimation approach
--------------------
The R draft uses `fixest::feols(y ~ x1 + x2 | Country + Year, cluster=~Country)`.
`fixest` defaults to clustering by the first fixed-effect (Country) whenever
fixed effects are present, even where the R code omits an explicit `cluster=`
argument -- so every model here uses country-clustered standard errors.

Two-way fixed effects are implemented as country + year dummy variables
(LSDV) fit with `statsmodels.OLS` + cluster-robust covariance, rather than
`linearmodels.PanelOLS`'s built-in demeaning: on this unbalanced 16-country
panel, PanelOLS's absorption-rank check flags the whole regressor block as
collinear with the fixed effects (a false positive -- manual two-way
demeaning confirms `treat_post` retains ~30% of its raw variance after
entity+year demeaning). LSDV is algebraically identical to two-way FE
(Frisch-Waugh-Lovell) and isn't affected by that check.

`treated`/`early_treated`/`late_treated` are time-invariant per country, so
they're collinear with the country dummies and dropped from every model's
regressor list before fitting -- exactly what `fixest` itself does
(reporting `NA` for those coefficients) rather than a simplification.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm

from . import config as cfg

PARALLEL_TREND_CUTOFF_YEAR = 2007  # R: last_pre_year <- 2007 (filter Year < 2008)


# ---------------------------------------------------------------------------
# 1. DiD data preparation
# ---------------------------------------------------------------------------


def prepare_did_data(merged_data: pd.DataFrame) -> pd.DataFrame:
    """R chunk ~lines 457-534. Restricts to the 16 treated/control countries and
    builds treated/post/treat_post/early_treated/late_treated/trade_openness.
    """
    df = merged_data.copy()
    df["country"] = df["country"].astype(str).str.strip().str.lower()

    early = [c.lower() for c in cfg.EARLY_ADOPTERS]
    late = [c.lower() for c in cfg.LATE_ADOPTERS]
    treated_list = [c.lower() for c in cfg.TREATED_COUNTRIES]
    control_list = [c.lower() for c in cfg.CONTROL_COUNTRIES]
    all_list = treated_list + control_list

    adoption_years = pd.DataFrame(
        {
            "country": treated_list,
            "adoption_year": [cfg.ADOPTION_YEARS[c] for c in cfg.TREATED_COUNTRIES],
        }
    )

    df = df[df["country"].isin(all_list)].copy()
    df = df.merge(adoption_years, on="country", how="left")

    df["treated"] = df["country"].isin(treated_list).astype(int)
    df["post"] = ((df["adoption_year"].notna()) & (df["year"] >= df["adoption_year"])).astype(int)
    df["treat_post"] = df["treated"] * df["post"]
    df["early_treated"] = df["country"].isin(early).astype(int)
    df["late_treated"] = df["country"].isin(late).astype(int)
    df["trade_openness"] = (df["exports"] + df["imports"]) / df["gdp"]
    return df


def did_setup_checks(did_data: pd.DataFrame):
    """R: print(unique(merged_data$Country)); table(is.na(adoption_year), treated)"""
    countries = sorted(did_data["country"].unique())
    crosstab = pd.crosstab(did_data["adoption_year"].isna(), did_data["treated"])
    return countries, crosstab


# ---------------------------------------------------------------------------
# 2. Parallel trends test (pre-treatment)
# ---------------------------------------------------------------------------


def parallel_trends_stats(did_data: pd.DataFrame, value_col: str) -> pd.DataFrame:
    """R: stat_summary(fun=mean, geom="line") + stat_summary(fun.data=mean_se, geom="ribbon")"""
    pre = did_data[(did_data["year"] < 2008) & did_data["treated"].isin([0, 1])]
    pre = pre.dropna(subset=[value_col])
    g = pre.groupby(["year", "treated"])[value_col].agg(["mean", "std", "count"]).reset_index()
    g["se"] = g["std"] / np.sqrt(g["count"])
    return g


def plot_parallel_trends(stats: pd.DataFrame, title: str, ylabel: str, save_path=None):
    fig, ax = plt.subplots(figsize=(8, 5))
    for t in [0, 1]:
        sub = stats[stats["treated"] == t].sort_values("year")
        if sub.empty:
            continue
        color = cfg.PARALLEL_TRENDS_COLORS[t]
        label = cfg.PARALLEL_TRENDS_LABELS[t]
        ax.plot(sub["year"], sub["mean"], color=color, linewidth=1.8, label=label)
        ax.fill_between(
            sub["year"], sub["mean"] - sub["se"], sub["mean"] + sub["se"], color=color, alpha=0.15, linewidth=0
        )
    ax.axvline(PARALLEL_TREND_CUTOFF_YEAR, linestyle="--", color="gray")
    ax.set_title(title)
    ax.set_xlabel("Year")
    ax.set_ylabel(ylabel)
    cfg.style_axes(ax)
    ax.legend(title="Group")
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150)
    return fig, ax


# ---------------------------------------------------------------------------
# Two-way fixed effects regression helper (LSDV + cluster-robust SE)
# ---------------------------------------------------------------------------


def fit_twfe(df: pd.DataFrame, y_col: str, x_cols: list, cluster_col: str = "country") -> sm.regression.linear_model.RegressionResultsWrapper:
    """Note on `post`/`treat_post`: in this dataset `post` is 0 for every control
    country (their `adoption_year` is always NaN), so `treated * post` equals
    `post` exactly wherever both are used together -- the two columns end up
    byte-identical. Rather than let OLS split an indeterminate coefficient
    arbitrarily between two identical columns, exact duplicates among `x_cols`
    are detected and the later one is dropped (reported as NA in `coef_table`),
    matching `fixest`'s own collinearity elimination.
    """
    sub = df[["country", "year", y_col] + x_cols].dropna().copy()

    kept, dropped = [], {}
    for col in x_cols:
        duplicate_of = next((k for k in kept if sub[col].equals(sub[k])), None)
        if duplicate_of is not None:
            dropped[col] = duplicate_of
        else:
            kept.append(col)

    entity_dummies = pd.get_dummies(sub["country"], prefix="c", drop_first=True, dtype=float)
    year_dummies = pd.get_dummies(sub["year"].astype(int), prefix="y", drop_first=True, dtype=float)

    X = pd.concat([sub[kept].astype(float), entity_dummies, year_dummies], axis=1)
    X = sm.add_constant(X)
    y = sub[y_col].astype(float)

    model = sm.OLS(y, X)
    res = model.fit(cov_type="cluster", cov_kwds={"groups": sub[cluster_col]})
    res.dropped_terms_ = dropped
    return res


def coef_table(res, terms: list) -> pd.DataFrame:
    """Coefficient/SE/CI table for `terms`; terms dropped in `fit_twfe` for exact
    collinearity show as NaN (mirrors fixest printing `NA` for those rows)."""
    dropped = getattr(res, "dropped_terms_", {})
    ci = res.conf_int()
    rows = {}
    for t in terms:
        if t in dropped:
            rows[t] = {"coef": np.nan, "std_err": np.nan, "p_value": np.nan, "ci_low": np.nan, "ci_high": np.nan}
        else:
            rows[t] = {
                "coef": res.params[t],
                "std_err": res.bse[t],
                "p_value": res.pvalues[t],
                "ci_low": ci.loc[t, 0],
                "ci_high": ci.loc[t, 1],
            }
    return pd.DataFrame(rows).T


# ---------------------------------------------------------------------------
# 3. Main DiD regressions (GDP growth / inflation / unemployment)
# ---------------------------------------------------------------------------

MAIN_CONTROLS = [
    "trade_openness",
    "renewable_energy_pct",
    "manufacturing_growth",
    "ores_metals_exports_pct",
    "population",
]
MAIN_REGRESSORS = ["post", "treat_post"] + MAIN_CONTROLS  # `treated` dropped: collinear w/ country FE

MAIN_OUTCOMES = {
    "gdp_growth": "GDP Growth",
    "inflation": "Inflation",
    "unemployment": "Unemployment",
}


def run_main_did_models(did_data: pd.DataFrame) -> dict:
    return {y: fit_twfe(did_data, y, MAIN_REGRESSORS) for y in MAIN_OUTCOMES}


# ---------------------------------------------------------------------------
# 3B. Event studies (dynamic DiD), treated countries only
# ---------------------------------------------------------------------------

EVENT_WINDOW = range(-5, 6)
EVENT_REF = -1


def build_event_study_data(did_data: pd.DataFrame, rel_year_col: str = "event_time") -> tuple:
    """R: event_time/Year_rel = Year - adoption_year for treated countries; filter to [-5,5].

    `i(Year_rel, treated, ref=-1)` (the second event study, R lines 706-716)
    interacts the relative-year dummies with `treated`, but on this
    treated-only subsample `treated` is always 1, so the interaction reduces
    to the same dummy set as the first event study -- both are built with
    this one function.
    """
    df = did_data[did_data["treated"] == 1].copy()
    df[rel_year_col] = df["year"] - df["adoption_year"]
    df = df[(df[rel_year_col] >= min(EVENT_WINDOW)) & (df[rel_year_col] <= max(EVENT_WINDOW))]

    dummy_cols = []
    for k in EVENT_WINDOW:
        if k == EVENT_REF:
            continue
        col = f"event_{k}"
        df[col] = (df[rel_year_col] == k).astype(int)
        dummy_cols.append(col)
    return df, dummy_cols


def run_event_study(did_data: pd.DataFrame, y_col: str) -> tuple:
    event_data, dummy_cols = build_event_study_data(did_data)
    res = fit_twfe(event_data, y_col, dummy_cols + MAIN_CONTROLS)
    return res, dummy_cols


def plot_event_study(res, dummy_cols: list, title: str, ylabel: str, save_path=None):
    """Equivalent of fixest's `iplot()`: point estimate + 95% CI per relative year,
    horizontal line at 0, vertical dashed line at the adoption year (t=0).
    """
    event_values = sorted(int(c.split("_")[1]) for c in dummy_cols)
    coefs = coef_table(res, [f"event_{k}" for k in event_values])

    fig, ax = plt.subplots(figsize=(8, 5))
    yerr = [(coefs["coef"] - coefs["ci_low"]).values, (coefs["ci_high"] - coefs["coef"]).values]
    ax.errorbar(event_values, coefs["coef"], yerr=yerr, fmt="o", color=cfg.COLOR_BLUE, ecolor="lightblue", capsize=3)
    ax.axhline(0, color="gray", linewidth=0.8)
    ax.axvline(0, linestyle="--", color="gray")
    ax.set_title(title)
    ax.set_xlabel("Years Since Carbon Pricing")
    ax.set_ylabel(ylabel)
    cfg.style_axes(ax)
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150)
    return fig, ax


# ---------------------------------------------------------------------------
# 3C. Early vs. late adopters comparison
# ---------------------------------------------------------------------------


def add_early_late_interactions(did_data: pd.DataFrame) -> pd.DataFrame:
    """R: i(post, early_treated, ref=0) + i(post, late_treated, ref=0)
    -- since `post` is binary with ref=0, each i() term reduces to a single
    interaction dummy (early_treated*post / late_treated*post).
    """
    df = did_data.copy()
    df["early_post"] = df["early_treated"] * df["post"]
    df["late_post"] = df["late_treated"] * df["post"]
    return df


EARLY_LATE_REGRESSORS = ["early_post", "late_post"] + MAIN_CONTROLS


def run_early_late_models(did_data: pd.DataFrame) -> dict:
    df = add_early_late_interactions(did_data)
    return {y: fit_twfe(df, y, EARLY_LATE_REGRESSORS) for y in MAIN_OUTCOMES}


# ---------------------------------------------------------------------------
# NA check by country
# ---------------------------------------------------------------------------


def na_counts_by_country(did_data: pd.DataFrame) -> pd.DataFrame:
    cols = ["gdp_growth", "inflation", "unemployment", "trade_openness"] + MAIN_CONTROLS[1:]
    return did_data.groupby("country")[cols].apply(lambda x: x.isna().sum())


# ---------------------------------------------------------------------------
# 4A. Placebo test (fake policy year)
# ---------------------------------------------------------------------------

FAKE_POLICY_YEAR = 2000
PLACEBO_CONTROLS = ["trade_openness", "renewable_energy_pct", "ores_metals_exports_pct", "population"]
PLACEBO_REGRESSORS = ["fake_post", "fake_treat_post"] + PLACEBO_CONTROLS  # note: no manufacturing_growth, matching R


def run_placebo_test(did_data: pd.DataFrame) -> sm.regression.linear_model.RegressionResultsWrapper:
    df = did_data.copy()
    df["fake_post"] = (df["year"] >= FAKE_POLICY_YEAR).astype(int)
    df["fake_treat_post"] = df["treated"] * df["fake_post"]
    return fit_twfe(df, "gdp_growth", PLACEBO_REGRESSORS)


# ---------------------------------------------------------------------------
# 4B. Sensitivity test: narrower (EU) control group
# ---------------------------------------------------------------------------


def run_sensitivity_test(merged_data: pd.DataFrame) -> sm.regression.linear_model.RegressionResultsWrapper:
    """R: filter(Selected_Country %in% c(early_adopters, eu_controls)) -- `Selected_Country`
    doesn't exist (only `Country`, already lowercased earlier in the script); this uses
    `country`. By this point in the R script `merged_data` has also already been
    overwritten with the 16-country DiD subset, so the EU comparators
    (Norway/Denmark/Austria/Poland/Czech Republic/Spain) -- none of which are in
    that 16-country list -- would never actually appear; this reconstructs the
    intended check by drawing the EU comparators from the full, unrestricted
    `merged_data` instead.
    """
    df = merged_data.copy()
    df["country"] = df["country"].astype(str).str.strip().str.lower()

    early = [c.lower() for c in cfg.EARLY_ADOPTERS]
    eu_controls = [c.lower() for c in cfg.EU_SENSITIVITY_CONTROLS]

    sub = df[df["country"].isin(early + eu_controls)].copy()

    adoption_years = pd.DataFrame({"country": early, "adoption_year": [cfg.ADOPTION_YEARS[c] for c in cfg.EARLY_ADOPTERS]})
    sub = sub.merge(adoption_years, on="country", how="left")

    sub["treated"] = sub["country"].isin(early).astype(int)
    sub["post"] = ((sub["adoption_year"].notna()) & (sub["year"] >= sub["adoption_year"])).astype(int)
    sub["treat_post"] = sub["treated"] * sub["post"]
    sub["trade_openness"] = (sub["exports"] + sub["imports"]) / sub["gdp"]

    return fit_twfe(sub, "gdp_growth", MAIN_REGRESSORS)
