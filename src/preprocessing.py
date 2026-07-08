"""Data loading + merge, mirroring the R draft's "1. DATA PREP" section.

R:
    colnames(df) <- make.names(colnames(df))
    merged_data <- clean_data %>%
      full_join(compliance_price, by = c("Country", "Year")) %>%
      full_join(emissions_data, by = c("Country", "Year"))
"""

import pandas as pd

from . import config as cfg


def load_economic_data() -> pd.DataFrame:
    """Load `clean data.xlsx` (World Bank economic indicators by country/year)."""
    econ = pd.read_excel(cfg.ECONOMIC_DATA_PATH)
    econ.columns = [c.strip() for c in econ.columns]
    econ = econ.rename(columns=cfg.ECON_COLUMN_MAP)
    econ["country"] = econ["country"].str.strip()

    # World Bank's ".." missing-value marker loads as text; coerce to numeric
    # (matches `as.numeric()` behaviour applied to this column later in the R draft).
    econ["renewable_energy_pct"] = pd.to_numeric(econ["renewable_energy_pct"], errors="coerce")
    return econ


def load_compliance_price() -> pd.DataFrame:
    """Load `Cleaned_Compliance_Price_Data.csv` (carbon tax/ETS by country/year)."""
    comp = pd.read_csv(cfg.COMPLIANCE_PRICE_PATH)
    comp = comp.rename(columns=cfg.COMPLIANCE_COLUMN_MAP)
    comp["year"] = comp["year"].astype(int)
    comp["average_carbon_tax"] = pd.to_numeric(comp["average_carbon_tax"], errors="coerce")
    comp["average_ets"] = pd.to_numeric(comp["average_ets"], errors="coerce")
    return comp[["country", "region", "year", "average_carbon_tax", "average_ets"]]


def load_emissions_data() -> pd.DataFrame:
    """Load `Organized_Emissions_Data.csv` (CO2 emissions by country/year)."""
    emis = pd.read_csv(cfg.EMISSIONS_DATA_PATH)
    return emis.rename(columns=cfg.EMISSIONS_COLUMN_MAP)


def build_merged_data() -> pd.DataFrame:
    """R: full_join(clean_data, compliance_price, by=c("Country","Year")) %>% full_join(emissions_data, ...)"""
    econ = load_economic_data()
    comp = load_compliance_price()
    emis = load_emissions_data()

    merged = econ.merge(comp, on=["country", "year"], how="outer")
    merged = merged.merge(emis, on=["country", "year"], how="outer")
    return merged
