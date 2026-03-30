import pandas as pd

TOPJOBS_FILE = "internships_with_skills_v2.csv"
COMPANY_FILE = "company_internships_with_skills.csv"
OUT_FILE = "final_internships_dataset.csv"

def main():
    df1 = pd.read_csv(TOPJOBS_FILE)
    df2 = pd.read_csv(COMPANY_FILE)

    for col in ["source", "title", "company", "location", "ad_url", "tech_skills", "description_text"]:
        if col not in df1.columns:
            df1[col] = ""
        if col not in df2.columns:
            df2[col] = ""

    combined = pd.concat([df1, df2], ignore_index=True)
    combined.drop_duplicates(subset=["title", "company", "ad_url"], inplace=True)
    combined.to_csv(OUT_FILE, index=False, encoding="utf-8")

    print(f"[✓] Saved {len(combined)} rows -> {OUT_FILE}")

if __name__ == "__main__":
    main()