import os
import pandas as pd
from collections import Counter

IN_CSV = "data/processed/tech_internships.csv"
OUT_CSV = "data/processed/skill_frequency.csv"

def main():
    df = pd.read_csv(IN_CSV)

    all_skills = []

    for skills in df["tech_skills"].fillna(""):
        skill_list = [s.strip() for s in skills.split(",") if s.strip()]
        all_skills.extend(skill_list)

    counter = Counter(all_skills)

    freq_df = pd.DataFrame(counter.items(), columns=["skill", "count"])
    freq_df = freq_df.sort_values("count", ascending=False)

    os.makedirs("data/processed", exist_ok=True)
    freq_df.to_csv(OUT_CSV, index=False)

    print("[✓] Saved:", OUT_CSV)
    print("\nTop 20 Skills:\n")
    print(freq_df.head(20))

if __name__ == "__main__":
    main()