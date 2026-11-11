"""ILO 2025 exposure index: from task level to ISCO groups (1 to 4 digits)."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "ILO_GenAI_exposure_ISCO08_2025.xlsx"
OUT = ROOT / "data" / "processed"


def load_tasks(path=RAW):
    tasks = pd.read_excel(path)
    tasks["isco4"] = tasks["ISCO_08"].astype(int)
    # shorter codes = first digits of the 4-digit code
    for k in (1, 2, 3):
        tasks[f"isco{k}"] = tasks["isco4"] // 10 ** (4 - k)
    return tasks


def aggregate(tasks, level):
    # mean and sd of the task scores in each group (no employment weights in the ILO file)
    key = f"isco{level}"
    g = tasks.groupby(key)
    out = pd.DataFrame({
        "exposure_mean_2025": g["score_2025"].mean(),
        "exposure_sd_2025": g["score_2025"].std(),
        "exposure_mean_2023": g["score_2023"].mean(),
        "n_tasks": g.size(),
        "n_occupations": g["isco4"].nunique(),
    })
    if level == 4:
        first = g.first()
        out["title"] = first["Title"]
        out["gradient_2025"] = first["potential25"]
        out["major_group"] = first["label1d"]
    return out.reset_index()


if __name__ == "__main__":
    # saves the ILO tables (public data, ok to commit)
    OUT.mkdir(parents=True, exist_ok=True)
    tasks = load_tasks()
    for level in (1, 2, 3, 4):
        table = aggregate(tasks, level)
        table.to_csv(OUT / f"ilo_isco{level}d.csv", index=False)
        print(level, "digits:", len(table), "groups")
