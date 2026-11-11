"""Loads the cleaned SHP file and adds the ILO exposure scores.

SHP file comes from 01_shp_cleaning.ipynb and stays local (never on GitHub).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


SHP_FILE = Path("data") / "processed" / "shp_population_income.parquet"
PROCESSED = Path("data") / "processed"  # ILO tables made by src/ilo_aggregate.py

# 3 for now (is3maj), put 4 when we get the detailed codes
ISCO_LEVEL = 3

# FSO regions (check codes in the SHP codebook)
REGION_LABELS = {
    1: "Lake Geneva", 2: "Espace Mittelland", 3: "Northwestern CH",
    4: "Zurich", 5: "Eastern CH", 6: "Central CH", 7: "Ticino",
}
ISCO1_LABELS = {
    "1": "Managers", "2": "Professionals", "3": "Technicians & associates",
    "4": "Clerical support", "5": "Service & sales", "6": "Agriculture",
    "7": "Craft & trades", "8": "Machine operators", "9": "Elementary",
    "0": "Armed forces",
}


def load_ilo(project_root: Path, level: int = ISCO_LEVEL) -> pd.DataFrame:
    key = f"isco{level}"
    ilo = pd.read_csv(project_root / PROCESSED / f"ilo_isco{level}d.csv")
    ilo[key] = ilo[key].astype(int).astype(str).str.zfill(level)
    return ilo


def load_analysis_data(project_root: Path, level: int = ISCO_LEVEL) -> tuple[pd.DataFrame, dict]:
    shp = pd.read_parquet(project_root / SHP_FILE)
    n_start = len(shp)

    # we keep only men and women (sex = 3 only in 2024, very few people)
    shp = shp[shp["sex"].isin([1, 2])].copy()
    n_sex = n_start - len(shp)

    key = f"isco{level}"
    shp[key] = shp[key].astype(str).str.strip().str.zfill(level)
    ilo = load_ilo(project_root, level)
    cols = [key, "exposure_mean_2025", "exposure_sd_2025", "exposure_mean_2023"]
    df = shp.merge(ilo[cols], on=key, how="left", validate="many_to_one")
    df["isco_code"] = df[key]

    matched = df["exposure_mean_2025"].notna()
    info = {
        "n_start": n_start,
        "n_sex_dropped": n_sex,
        "n_unmatched": int((~matched).sum()),
        "share_matched": float(matched.mean()),
        "unmatched_codes": df.loc[~matched, key].value_counts().head(10),
        "level": level,
        "n_codes": int(df.loc[matched, key].nunique()),
    }
    df = df[matched].copy()

    df["isco1"] = df["isco_code"].str[0]
    df["isco1_label"] = df["isco1"].map(ISCO1_LABELS)
    df["region_label"] = df["region"].map(REGION_LABELS).fillna(df["region"].astype(str))
    df["female"] = (df["sex"] == 2).astype(int)
    df["post_chatgpt"] = (df["year"] >= 2023).astype(int)
    df["group"] = np.where(df["tertiary"] == 1, "Tertiary", "Non-tertiary")
    return df, info

