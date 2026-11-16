# SHP cleaning: person, income and household files, 2016-2024
# The SHP files are not shared (FORS contract) and the output starts with shp_ (ignored by Git)

import pandas as pd
import numpy as np

PATH_P = "PASTE_THE_PATH_HERE/shplong_p_user.dta"
PATH_INC = "PASTE_THE_PATH_HERE/imputed_income_pers_long_shp.dta"
PATH_H = "PASTE_THE_PATH_HERE/shplong_h_user.dta"
OUTPUT = "shp_population_income.parquet"

# load only the columns we need, keeping the numeric codes
COLS_P = ["idpers", "year", "idhous", "pdate", "age", "sex", "isced", "pe31",
          "wstat", "pw29", "pw39", "pw42", "is3maj", "noga2m", "iempyg", "wicss"]
COLS_INC = ["idpers", "year", "iempyni", "impempyn", "cpi2020"]
COLS_H = ["idhous", "year", "canton", "region", "com3_"]

p = pd.read_stata(PATH_P, columns=COLS_P, convert_categoricals=False)
inc = pd.read_stata(PATH_INC, columns=COLS_INC, convert_categoricals=False)
h = pd.read_stata(PATH_H, columns=COLS_H, convert_categoricals=False)
print(p.shape, inc.shape, h.shape)

# keep 2016-2024 (2025 is a beta release)
p = p[(p["year"] >= 2016) & (p["year"] <= 2024)].copy()
inc = inc[(inc["year"] >= 2016) & (inc["year"] <= 2024)].copy()
h = h[(h["year"] >= 2016) & (h["year"] <= 2024)].copy()
print(p["year"].value_counts().sort_index())

# negative SHP codes (-1 does not know, -2 no answer, -3 inapplicable...) become missing
p_codes = p.copy()
for df in [p, inc, h]:
    num = df.select_dtypes("number").columns.drop(["idpers", "idhous", "year"], errors="ignore")
    df[num] = df[num].where(df[num] >= 0, np.nan)
print((p.isna().mean() * 100).round(1).sort_values(ascending=False))

# check the codes used in the filters (counts only)
for col in ["sex", "isced", "wstat", "pw29", "pw39"]:
    print(p_codes[col].value_counts(dropna=False).sort_index())

# codes checked in the SHP codebook
CODES_TERTIARY = [51, 52, 60]   # ISCED 5A, 5B and 6
CODES_EMPLOYED = [1]            # wstat: employed
CODES_EMPLOYEE = [5]            # pw29: employee
CODE_FULL_TIME = 2              # pw39: full time

# merge income (person and year) and household (household and year)
df = p.merge(inc, on=["idpers", "year"], how="left", validate="one_to_one", indicator=True)
print(df["_merge"].value_counts())
df = df.drop(columns="_merge")

df = df.merge(h, on=["idhous", "year"], how="left", validate="many_to_one", indicator=True)
print(df["_merge"].value_counts())
df = df.drop(columns="_merge")

# filters: employed, employees, aged 25-65, known occupation
steps = [("Start", len(df))]
df = df[df["wstat"].isin(CODES_EMPLOYED)];  steps.append(("Employed persons", len(df)))
df = df[df["pw29"].isin(CODES_EMPLOYEE)];   steps.append(("Employees", len(df)))
df = df[df["age"].between(25, 65)];         steps.append(("Aged 25-65", len(df)))
df = df[df["is3maj"].notna()];              steps.append(("Known ISCO occupation", len(df)))
print(pd.DataFrame(steps, columns=["step", "rows left"]))

# new variables
df["tertiary"] = df["isced"].isin(CODES_TERTIARY).astype(int)
df["tertiary_type"] = df["isced"].map({51: "university", 60: "university", 52: "higher_vocational"})
df["young"] = df["age"].between(25, 34).astype(int)
df["isco3"] = df["is3maj"].astype(int).astype(str).str.zfill(3)  # text, so 011 stays 011

df["activity_rate"] = np.where(df["pw39"] == CODE_FULL_TIME, 100, df["pw42"])
df["income_real"] = df["iempyni"] * 100 / df["cpi2020"]            # 2020 francs
df["income_fte"] = df["income_real"] * 100 / df["activity_rate"]   # full-time equivalent

# remove zero incomes, activity rates below 20% and the 1% extremes
df = df[df["income_fte"] > 0]
df = df[df["activity_rate"] >= 20]
bounds = df["income_fte"].quantile([0.01, 0.99])
df = df[df["income_fte"].between(bounds[0.01], bounds[0.99])]
print("Bounds (CHF):", bounds.round(0).tolist())

df["log_income"] = np.log(df["income_fte"])

# checks (expected: 40,796 rows, 10,076 persons) and save
print(pd.crosstab(df["year"], [df["tertiary"], df["young"]]))
print("Rows:", len(df), "| persons:", df["idpers"].nunique())
print("Imputed incomes (%):", round((df["impempyn"] > 0).mean() * 100, 1))

df.to_parquet(OUTPUT, index=False)
