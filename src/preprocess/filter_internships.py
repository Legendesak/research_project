import pandas as pd
import re

IN_CSV = "data/processed/topjobs_master.csv"
OUT_CSV = "data/processed/topjobs_internships.csv"

PAT = re.compile(r"\b(intern|internship|trainee|graduate trainee|management trainee)\b", re.I)

def main():
    df = pd.read_csv(IN_CSV)
    df["is_internship"] = df["title"].fillna("").apply(lambda x: bool(PAT.search(x)))
    interns = df[df["is_internship"]].copy()
    interns.to_csv(OUT_CSV, index=False)
    print(f"[✓] Intern/trainee ads: {len(interns)} → {OUT_CSV}")

if __name__ == "__main__":
    main()