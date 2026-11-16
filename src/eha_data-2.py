"""FSO survey of higher education graduates (EHA): standardized gross annual income
(full-time equivalent) one year after graduation, graduates working in Switzerland.
- TA3E61-1: by type of school and exam level, graduation years 2002-2024 (real francs)
- TA3E61-2: university graduates by exam level and field of study, graduation year 2024
- TA3E61-4: by type of school, exam level and sex, graduation year 2024"""
from pathlib import Path
import pandas as pd

EHA_FILE = Path("data") / "raw" / "EHA_graduates_income.xlsx"
SHEET = "TA3E61-1"
FIRST_COL_SWITZERLAND = 16  # columns 4-15 = all workplaces, 16-27 = workplace in Switzerland

SCHOOLS = {"HEU": "University", "HES": "University of applied sciences", "HEP": "University of teacher education"}
LEVELS = {"Bachelor": "Bachelor", "Master": "Master", "Doctorat": "Doctorate",
          "Diplôme d'enseignement": "Teaching diploma"}
STATS = {"1. quartile": "q1", "Médiane": "median", "3. quartile": "q3"}
FIELDS = {"Total": "Total", "Sciences humaines et sociales": "Humanities and social sciences",
          "Sciences économiques": "Economics and business", "Droit": "Law",
          "Sciences exactes et naturelles": "Exact and natural sciences",
          "Médecine et pharmacie": "Medicine and pharmacy", "Sciences techniques": "Technical sciences",
          "Interdisciplinaire et autre": "Interdisciplinary and other"}
SEXES = {"Total": "Total", "Homme": "Men", "Femme": "Women"}


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


def load_eha_field(project_root: Path) -> pd.DataFrame:
    # TA3E61-2: columns 8, 10, 12 = q1, median, q3 for graduates working in Switzerland
    raw = pd.read_excel(project_root / EHA_FILE, sheet_name="TA3E61-2", header=None)
    table = raw.iloc[6:30, [0, 1, 8, 10, 12]].copy()
    table.columns = ["exam_level", "field", "q1", "median", "q3"]
    table["exam_level"] = table["exam_level"].ffill().map(LEVELS)
    table["field"] = table["field"].str.replace("\xa0", " ").str.strip().map(FIELDS)
    for c in ["q1", "median", "q3"]:
        table[c] = pd.to_numeric(table[c], errors="coerce")  # "**" = fewer than 25 cases -> NaN
    table["school_type"] = "University"
    table["graduation_year"] = 2024
    return table[["school_type", "exam_level", "field", "graduation_year", "q1", "median", "q3"]]


def load_eha_sex(project_root: Path) -> pd.DataFrame:
    # TA3E61-4: columns 9, 11, 13 = q1, median, q3 for graduates working in Switzerland
    raw = pd.read_excel(project_root / EHA_FILE, sheet_name="TA3E61-4", header=None)
    table = raw.iloc[6:24, [0, 1, 2, 9, 11, 13]].copy()
    table.columns = ["school_type", "exam_level", "sex", "q1", "median", "q3"]
    table["school_type"] = table["school_type"].ffill().map(SCHOOLS)
    table["exam_level"] = table["exam_level"].ffill().map(LEVELS)
    table["sex"] = table["sex"].map(SEXES)
    for c in ["q1", "median", "q3"]:
        table[c] = pd.to_numeric(table[c], errors="coerce")
    table["graduation_year"] = 2024
    return table[["school_type", "exam_level", "sex", "graduation_year", "q1", "median", "q3"]]


def load_eha_processed(project_root: Path) -> pd.DataFrame:
    # clean tables made by running this file (see below)
    processed = project_root / "data" / "processed"
    return (pd.read_csv(processed / "eha_income_by_school_level.csv"),
            pd.read_csv(processed / "eha_income_by_field_2024.csv"),
            pd.read_csv(processed / "eha_income_by_sex_2024.csv"))


if __name__ == "__main__":
    # saves a clean table (public data, ok to commit)
    root = Path(__file__).resolve().parents[1]
    processed = root / "data" / "processed"
    load_eha(root).to_csv(processed / "eha_income_by_school_level.csv", index=False)
    load_eha_field(root).to_csv(processed / "eha_income_by_field_2024.csv", index=False)
    load_eha_sex(root).to_csv(processed / "eha_income_by_sex_2024.csv", index=False)
    print("saved 3 EHA tables in", processed)
