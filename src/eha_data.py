"""FSO survey of higher education graduates (EHA), table TA3E61-1: standardized
gross annual income (full-time equivalent, real francs) one year after graduation,
by type of school and exam level, graduation years 2002-2024."""
from pathlib import Path
import pandas as pd

EHA_FILE = Path("data") / "raw" / "EHA_graduates_income.xlsx"
SHEET = "TA3E61-1"
FIRST_COL_SWITZERLAND = 16  # columns 4-15 = all workplaces, 16-27 = workplace in Switzerland

SCHOOLS = {"HEU": "University", "HES": "University of applied sciences", "HEP": "University of teacher education"}
LEVELS = {"Bachelor": "Bachelor", "Master": "Master", "Doctorat": "Doctorate",
          "Diplôme d'enseignement": "Teaching diploma"}
STATS = {"1. quartile": "q1", "Médiane": "median", "3. quartile": "q3"}


def load_eha(project_root: Path) -> pd.DataFrame:
    raw = pd.read_excel(project_root / EHA_FILE, sheet_name=SHEET, header=None)

    # row 4 holds the graduation years, e.g. "2016c+" -> 2016
    year_cols = list(range(FIRST_COL_SWITZERLAND, raw.shape[1]))
    years = [int(str(raw.iloc[4, c])[:4]) for c in year_cols]

    table = raw.iloc[5:41].copy()
    table[0] = table[0].ffill()  # school type is written only on its first row
    table[1] = table[1].ffill()  # exam level too
    table = table[table[3].isin(STATS)]  # keep quartile/median rows, drop the CV rows

    rows = []
    for _, r in table.iterrows():
        for c, year in zip(year_cols, years):
            rows.append({
                "school_type": SCHOOLS[r[0]],
                "exam_level": LEVELS[r[1]],
                "graduation_year": year,
                "statistic": STATS[r[3]],
                # "." = no observation, "**" = fewer than 25 cases -> NaN
                "income": pd.to_numeric(r[c], errors="coerce"),
            })
    long = pd.DataFrame(rows)

    # one row per school type, exam level and year, with q1, median and q3 as columns
    wide = long.pivot_table(index=["school_type", "exam_level", "graduation_year"],
                            columns="statistic", values="income").reset_index()
    wide.columns.name = None
    return wide[["school_type", "exam_level", "graduation_year", "q1", "median", "q3"]]


def load_eha_processed(project_root: Path) -> pd.DataFrame:
    # clean table made by running this file (see below)
    return pd.read_csv(project_root / "data" / "processed" / "eha_income_by_school_level.csv")


if __name__ == "__main__":
    # saves a clean table (public data, ok to commit)
    root = Path(__file__).resolve().parents[1]
    out = root / "data" / "processed" / "eha_income_by_school_level.csv"
    load_eha(root).to_csv(out, index=False)
    print("saved", out)
