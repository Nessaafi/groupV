"""Loads the cleaned SHP file and adds the ILO exposure scores.

SHP file comes from src/01_shp_cleaning.py and stays local (never on GitHub).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


SHP_FILE = Path("data") / "processed" / "shp_population_income.parquet"
PROCESSED = Path("data") / "processed"  # ILO tables made by src/ilo_aggregate.py

# 4 = detailed codes from the SHP add-on (additional contract), 3 = standard release (is3maj)
ISCO_LEVEL = 4
ADDON_NAME = "SHP_EXT_ISCO4_OCCUPA_USER.dta"  # add-on file, stays local (never on GitHub)

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


def load_isco4(project_root: Path) -> pd.DataFrame:
    """4-digit ISCO codes of the main job, one row per person and year (from the SHP add-on)."""
    found = list(Path(project_root).rglob(ADDON_NAME))
    if not found:
        raise FileNotFoundError(f"{ADDON_NAME} not found in the project folder")
    addon = pd.read_stata(found[0], convert_categoricals=False)
    cols = [f"IS4MAJ{y}" for y in range(16, 25)]  # one column per wave, 2016-2024
    addon = addon.melt(id_vars="idpers", value_vars=cols, var_name="variable", value_name="is4maj")
    addon["year"] = 2000 + addon["variable"].str[-2:].astype(int)
    addon.loc[addon["is4maj"] < 0, "is4maj"] = np.nan  # negative = missing in the SHP
    addon = addon.dropna(subset=["is4maj"])
    addon["isco4"] = addon["is4maj"].astype(int).astype(str).str.zfill(4)
    return addon[["idpers", "year", "isco4"]]


def add_exposure_isco4(shp: pd.DataFrame, project_root: Path) -> pd.DataFrame:
    """Exposure at 4 digits; vague codes (e.g. 2500) get the score of the known group (25)."""
    shp = shp.merge(load_isco4(project_root), on=["idpers", "year"], how="left",
                    validate="one_to_one")
    cols = ["exposure_mean_2025", "exposure_sd_2025", "exposure_mean_2023"]

    # scores of every ILO group, at 4, 3, 2 and 1 digits
    scores = []
    for k in [4, 3, 2, 1]:
        ilo_k = load_ilo(project_root, k).rename(columns={f"isco{k}": "code"})
        scores.append(ilo_k[["code"] + cols])
    scores = pd.concat(scores).set_index("code")

    # code used: the 4-digit code if the ILO knows it, otherwise the known part of the code
    # (2500 -> "25"); if the add-on has no code, the 3-digit code of the standard release
    code = shp["isco4"].copy()
    unknown = code.notna() & ~code.isin(scores.index)
    code[unknown] = code[unknown].str.rstrip("0")
    code = code.fillna(shp["isco3"])
    shp["isco_code"] = code
    shp["exposure_source"] = np.where(shp["isco4"].isna(), "isco3",
                                      np.where(unknown, "group", "isco4"))
    return shp.join(scores, on="isco_code")


def load_analysis_data(project_root: Path, level: int = ISCO_LEVEL) -> tuple[pd.DataFrame, dict]:
    shp = pd.read_parquet(project_root / SHP_FILE)
    n_start = len(shp)

    # we keep only men and women (sex = 3 only in 2024, very few people)
    shp = shp[shp["sex"].isin([1, 2])].copy()
    n_sex = n_start - len(shp)

    shp["isco3"] = shp["isco3"].astype(str).str.strip().str.zfill(3)
    if level == 4:
        df = add_exposure_isco4(shp, project_root)
        key = "isco_code"
    else:
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
    if level == 4:
        info["source"] = df.loc[matched, "exposure_source"].value_counts()
    df = df[matched].copy()

    df["isco1"] = df["isco_code"].str[0]
    df["isco1_label"] = df["isco1"].map(ISCO1_LABELS)
    df["region_label"] = df["region"].map(REGION_LABELS).fillna(df["region"].astype(str))
    df["female"] = (df["sex"] == 2).astype(int)
    df["post_chatgpt"] = (df["year"] >= 2023).astype(int)
    df["group"] = np.where(df["tertiary"] == 1, "Tertiary", "Non-tertiary")
    return df, info
