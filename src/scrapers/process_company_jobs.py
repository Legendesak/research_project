import pandas as pd
from skill_pipeline_v2.src.nlp.extract_skills_v2 import extract_skills

IN_CSV = "company_internships_detailed.csv"
OUT_CSV = "company_internships_with_skills.csv"

def main():
    df = pd.read_csv(IN_CSV)

    tech_skills = []
    soft_skills = []
    all_skills = []
    normalized = []

    for _, row in df.iterrows():
        text = f"{row.get('title', '')} {row.get('description_text', '')}"
        res = extract_skills(text)

        tech_skills.append(", ".join(res["tech_skills"]))
        soft_skills.append(", ".join(res["soft_skills"]))
        all_skills.append(", ".join(res["all_skills"]))
        normalized.append(res["normalized_text"])

    df["normalized_text"] = normalized
    df["tech_skills"] = tech_skills
    df["soft_skills"] = soft_skills
    df["skills_all"] = all_skills

    df.to_csv(OUT_CSV, index=False, encoding="utf-8")
    print(f"[✓] Saved {len(df)} rows -> {OUT_CSV}")

if __name__ == "__main__":
    main()