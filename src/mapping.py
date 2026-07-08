"""World choropleth maps -- R draft's "#Map" section (`rworldmap`).

R's `joinCountryData2Map(..., joinCode="NAME", nameJoinColumn="Country")`
matches by country name and silently drops/warns about any country it can't
match to a map polygon. `plotly` needs ISO-3 codes for a reliable match, so
`COUNTRY_TO_ISO3` maps the World Bank-style names in `clean data.xlsx` to
their ISO-3 codes; any country not in this dict (e.g. "European Union", which
isn't a single polygon) is dropped the same way `joinCountryData2Map` would
drop it.

Note: the R draft filters `Year == 2024` here but titles both maps
"... (2023)" -- that mismatch is in the source itself and is reproduced
literally rather than silently corrected.
"""

import pandas as pd
import plotly.express as px

from . import config as cfg

COUNTRY_TO_ISO3 = {
    "Albania": "ALB", "Argentina": "ARG", "Australia": "AUS", "Austria": "AUT",
    "Belgium": "BEL", "Bolivia": "BOL", "Brazil": "BRA", "Bulgaria": "BGR",
    "Canada": "CAN", "Chile": "CHL", "China": "CHN", "Colombia": "COL",
    "Croatia": "HRV", "Denmark": "DNK", "Ecuador": "ECU",
    "Egypt, Arab Rep.": "EGY", "Estonia": "EST", "Finland": "FIN",
    "France": "FRA", "Germany": "DEU", "Greece": "GRC", "Hungary": "HUN",
    "Iceland": "ISL", "India": "IND", "Indonesia": "IDN", "Ireland": "IRL",
    "Italy": "ITA", "Japan": "JPN", "Kazakhstan": "KAZ", "Korea, Rep.": "KOR",
    "Latvia": "LVA", "Liechtenstein": "LIE", "Lithuania": "LTU",
    "Luxembourg": "LUX", "Malaysia": "MYS", "Mexico": "MEX",
    "Montenegro": "MNE", "Morocco": "MAR", "Netherlands": "NLD",
    "New Zealand": "NZL", "Norway": "NOR", "Panama": "PAN", "Paraguay": "PRY",
    "Peru": "PER", "Poland": "POL", "Portugal": "PRT", "Romania": "ROU",
    "Russian Federation": "RUS", "Saudi Arabia": "SAU", "Singapore": "SGP",
    "Slovak Republic": "SVK", "Slovenia": "SVN", "South Africa": "ZAF",
    "Spain": "ESP", "Sweden": "SWE", "Switzerland": "CHE", "Thailand": "THA",
    "Tunisia": "TUN", "Turkiye": "TUR", "United Arab Emirates": "ARE",
    "United Kingdom": "GBR", "United States": "USA",
}

LATEST_YEAR = 2024


def latest_year_map_data(merged_data: pd.DataFrame) -> pd.DataFrame:
    df = merged_data[merged_data["year"] == LATEST_YEAR].copy()
    df["iso3"] = df["country"].map(COUNTRY_TO_ISO3)
    return df.dropna(subset=["iso3"])


def plot_carbon_tax_map(merged_data: pd.DataFrame, save_path=None):
    df = latest_year_map_data(merged_data)
    fig = px.choropleth(
        df, locations="iso3", color="average_carbon_tax", color_continuous_scale="Blues",
        title="Global Carbon Tax Intensity (2023)", labels={"average_carbon_tax": "Carbon Tax"},
    )
    fig.update_layout(paper_bgcolor="white", plot_bgcolor="white")
    if save_path:
        fig.write_image(str(save_path), width=1100, height=650, scale=2)
    return fig


def plot_ets_map(merged_data: pd.DataFrame, save_path=None):
    df = latest_year_map_data(merged_data)
    fig = px.choropleth(
        df, locations="iso3", color="average_ets", color_continuous_scale="Reds",
        title="Global ETS Intensity (2023)", labels={"average_ets": "ETS Price"},
    )
    fig.update_layout(paper_bgcolor="white", plot_bgcolor="white")
    if save_path:
        fig.write_image(str(save_path), width=1100, height=650, scale=2)
    return fig
