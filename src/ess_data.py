"""FSO wage survey (ESS), table T17: median gross monthly wage by ISCO 2-digit
occupation, age group and sex (private and public sectors), one sheet per year."""
from pathlib import Path
import pandas as pd

ESS_FILE = Path("data") / "raw" / "ESS_T17_wage_by_occupation_age_sex.xlsx"
YEARS = [2012, 2014, 2016, 2018, 2020, 2022, 2024]

# columns of the sheet: code, label, then Total/Women/Men for each age group
COLS = {0: "code", 1: "label", 3: "all_ages", 6: "age_29_less", 9: "age_30_49", 12: "age_50_plus"}


def load_ess(project_root: Path, year: int) -> pd.DataFrame:
    raw = pd.read_excel(project_root / ESS_FILE, sheet_name=str(year), header=None)
    df = raw.iloc[7:, list(COLS)].rename(columns=COLS)
    # keep only the 2-digit occupation rows (sub-major groups)
    df = df[df["code"].astype(str).str.fullmatch(r"\d{2}")].copy()
    df["isco2"] = df["code"].astype(int)
    for c in ["all_ages", "age_29_less", "age_30_49", "age_50_plus"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")  # "*" = too few data -> NaN
    df["year"] = year
    return df.drop(columns="code")


def load_ess_all(project_root: Path) -> pd.DataFrame:
    return pd.concat([load_ess(project_root, y) for y in YEARS], ignore_index=True)


def load_ess_processed(project_root: Path) -> pd.DataFrame:
    # clean table made by running this file (see below)
    return pd.read_csv(project_root / "data" / "processed" / "ess_t17_wage_by_occupation_age.csv")


if __name__ == "__main__":
    # saves a clean long table (public data, ok to commit)
    root = Path(__file__).resolve().parents[1]
    out = root / "data" / "processed" / "ess_t17_wage_by_occupation_age.csv"
    load_ess_all(root).to_csv(out, index=False)
    print("saved", out)
