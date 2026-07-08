"""Paths, column aliases, labels, colors, and the shared plotting theme.

Translated from `draft stats definitivo.Rmd`. The R draft runs
`colnames(df) <- make.names(colnames(df))` on every dataset, which mangles
names like "GDP (current US$)" into "GDP..current.US..". Rather than
reproduce that literally, this uses readable snake_case aliases for the same
underlying variables (see `ECON_COLUMN_MAP` / `VARIABLE_LABELS` below) --
same data, same calculations, legible code.
"""

from pathlib import Path

import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
FIGURES_DIR = OUTPUT_DIR / "figures"
TABLES_DIR = OUTPUT_DIR / "tables"

ECONOMIC_DATA_PATH = DATA_DIR / "clean data.xlsx"
COMPLIANCE_PRICE_PATH = DATA_DIR / "Cleaned_Compliance_Price_Data.csv"
EMISSIONS_DATA_PATH = DATA_DIR / "Organized_Emissions_Data.csv"

FIGURES_DIR.mkdir(parents=True, exist_ok=True)
TABLES_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Column aliases (clean_data.xlsx -> snake_case)
# ---------------------------------------------------------------------------
ECON_COLUMN_MAP = {
    "Country": "country",
    "Country Code": "country_code",
    "Year": "year",
    "Time Code": "time_code",
    "GDP (current US$)": "gdp",
    "GDP growth (annual %)": "gdp_growth",
    "GDP per capita (current US$)": "gdp_per_capita",
    "GDP per capita growth (annual %)": "gdp_per_capita_growth",
    "Inflation, consumer prices (annual %)": "inflation",
    "Unemployment, total (% of total labor force) (national estimate)": "unemployment",
    "Manufacturing, value added (annual % growth)": "manufacturing_growth",
    "Merchandise exports (current US$)": "exports",
    "Ores and metals exports (% of merchandise exports)": "ores_metals_exports_pct",
    "Ores and metals imports (% of merchandise imports)": "ores_metals_imports_pct",
    "Merchandise imports (current US$)": "imports",
    "Carbon dioxide (CO2) emissions (total) excluding LULUCF (Mt CO2e)": "co2_emissions_total",
    "Renewable energy consumption (% of total final energy consumption)": "renewable_energy_pct",
    "Population": "population",
}

COMPLIANCE_COLUMN_MAP = {
    "Country": "country",
    "Region": "region",
    "Year": "year",
    "average_carbon_tax": "average_carbon_tax",
    "average_ETS": "average_ets",
}

EMISSIONS_COLUMN_MAP = {
    "Year": "year",
    "Country": "country",
    "Emissions": "emissions",
}

# Readable labels for the scatter-plot loop (R draft used the raw mangled
# column name as the axis label/title text -- these are used instead).
VARIABLE_LABELS = {
    "gdp": "GDP (current US$)",
    "gdp_per_capita": "GDP per capita (current US$)",
    "inflation": "Inflation, consumer prices (annual %)",
    "unemployment": "Unemployment (% of total labor force)",
    "exports": "Merchandise exports (current US$)",
    "imports": "Merchandise imports (current US$)",
}

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------
COLOR_BLUE = "blue"          # R "blue" == "#0000FF"
COLOR_RED = "red"            # R "red" == "#FF0000"
COLOR_STEELBLUE = "steelblue"  # R "steelblue" == "#4682B4", same name in matplotlib
COLOR_GREEN = "green"        # R "green" == "#00FF00"
COLOR_BLACK = "black"

# ggplot2's default discrete hue palette for n=4 categories
# (hues at 15/105/195/285 degrees, chroma=100, luminance=65)
GGPLOT_HUE_4 = ["#F8766D", "#7CAE00", "#00BFC4", "#C77CFF"]

# Parallel-trends plot colors, matched literally to the R draft
PARALLEL_TRENDS_COLORS = {0: "#E57373", 1: "#64B5F6"}
PARALLEL_TRENDS_LABELS = {0: "Control", 1: "Treated"}

GRID_COLOR = "#EBEBEB"  # ggplot2 theme_minimal() panel.grid colour ("grey92")


def apply_theme_minimal() -> None:
    """Set matplotlib rcParams to visually match ggplot2's theme_minimal()."""
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
            "font.family": "sans-serif",
            "font.size": 11,
            "axes.titlesize": 13,
            "axes.titleweight": "normal",
            "axes.labelsize": 11,
            "axes.edgecolor": "white",
            "axes.linewidth": 0,
            "axes.grid": True,
            "grid.color": GRID_COLOR,
            "grid.linewidth": 0.8,
            "axes.axisbelow": True,
            "xtick.color": "black",
            "ytick.color": "black",
            "xtick.major.size": 0,
            "ytick.major.size": 0,
            "legend.frameon": False,
        }
    )


def style_axes(ax) -> None:
    """Strip spines/ticks the way theme_minimal() does, per-axes."""
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(length=0)
    ax.set_axisbelow(True)


# ---------------------------------------------------------------------------
# Difference-in-differences country groups (Section 3 of the R draft)
# ---------------------------------------------------------------------------
EARLY_ADOPTERS = ["Finland", "Sweden", "Ireland", "New Zealand"]
LATE_ADOPTERS = ["France", "Canada", "Korea, Rep.", "Japan"]
TREATED_COUNTRIES = EARLY_ADOPTERS + LATE_ADOPTERS
CONTROL_COUNTRIES = [
    "United States",
    "Belgium",
    "Turkiye",
    "Italy",
    "Saudi Arabia",
    "Lithuania",
    "Portugal",
    "Greece",
]
ALL_DID_COUNTRIES = TREATED_COUNTRIES + CONTROL_COUNTRIES

# Adoption years, positionally matched to TREATED_COUNTRIES order
ADOPTION_YEARS = {
    country: year
    for country, year in zip(
        TREATED_COUNTRIES, [1990, 1991, 2010, 2008, 2014, 2019, 2015, 2016]
    )
}

EU_SENSITIVITY_CONTROLS = ["Norway", "Denmark", "Austria", "Poland", "Czech Republic", "Spain"]
