import os
from pathlib import Path
import pandas as pd

from src.nlp.extract_skills_v2 import extract_skills
from src.nlp.skill_dictionary_v2 import TECH_STRONG_TERMS
from src.nlp.skill_dictionary_v2 import SKILL_CATEGORIES, CORE_TECH_SKILLS

# Change this if your file is somewhere else
IN_CSV = "/Users/ajithkumar/Desktop/scraperr/data/processed/topjobs_internships.csv"
OUT_DIR = "output"

def detect_text_column(df: pd.DataFrame) -> str:
    preferred = ["ocr_text", "ocr_text_raw", "poster_text", "text", "description"]
    for c in preferred:
        if c in df.columns:
            return c
    for c in df.columns:
        if "ocr" in c.lower():
            return c
    raise ValueError("No OCR text column found.")

def tech_score(title: str, text: str, tech_skills: list[str]) -> int:
    title = str(title or "").lower()
    text = str(text or "").lower()
    score = 0

    title_patterns = [
        "software", "developer", "engineer", "web", "mobile", "data", "it ", " it",
        "qa", "cloud", "devops", "security", "network", "machine learning", "ai"
    ]
    for p in title_patterns:
        if p in title:
            score += 2

    text_patterns = [
        "programming", "developer", "software", "web", "api", "database", "frontend",
        "backend", "mobile", "cloud", "network", "cyber", "machine learning", "data science"
    ]
    for p in text_patterns:
        if p in text:
            score += 1

    strong_skill_hits = sum(1 for s in tech_skills if s in TECH_STRONG_TERMS)
    score += min(strong_skill_hits, 5)

    return score

def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    df = pd.read_csv(IN_CSV)
    text_col = detect_text_column(df)

    tech_list = []
    soft_list = []
    all_list = []
    category_list = []
    norm_list = []
    score_list = []
    keep_list = []

    for _, row in df.iterrows():
        raw_text = str(row.get(text_col, "") or "")
        title = str(row.get("title", "") or "")

        res = extract_skills(raw_text)

        tech_skills = res["tech_skills"]
        score = tech_score(title, res["normalized_text"], tech_skills)
        keep = score >= 3

        tech_list.append(", ".join(tech_skills))
        soft_list.append(", ".join(res["soft_skills"]))
        all_list.append(", ".join(res["all_skills"]))
        category_list.append("; ".join([f"{k}: {', '.join(v)}" for k, v in res["categories"].items()]))
        norm_list.append(res["normalized_text"])
        score_list.append(score)
        keep_list.append(keep)

    df["normalized_text"] = norm_list
    df["tech_skills"] = tech_list
    df["soft_skills"] = soft_list
    df["skills_all"] = all_list
    df["skill_categories"] = category_list
    df["tech_score"] = score_list
    df["is_tech_v2"] = keep_list

    out_all = Path(OUT_DIR) / "internships_with_skills_v2.csv"
    df.to_csv(out_all, index=False, encoding="utf-8")

    tech_df = df[df["is_tech_v2"]].copy()
    out_tech = Path(OUT_DIR) / "tech_internships_v2.csv"
    tech_df.to_csv(out_tech, index=False, encoding="utf-8")

    # skill frequency
    all_skills = []
    for skills in tech_df["tech_skills"].fillna(""):
        parsed = [s.strip() for s in skills.split(",") if s.strip()]
        parsed = [s for s in parsed if s in CORE_TECH_SKILLS]
        all_skills.extend(parsed)

    freq_df = (
        pd.Series(all_skills, dtype="object")
        .value_counts()
        .rename_axis("skill")
        .reset_index(name="count")
    )
    freq_df.to_csv(Path(OUT_DIR) / "skill_frequency_v2.csv", index=False, encoding="utf-8")

    # category frequency
    cat_rows = []
    for _, row in tech_df.iterrows():
        skill_str = str(row.get("tech_skills", "") or "")
        for s in [x.strip() for x in skill_str.split(",") if x.strip()]:
            cat_rows.append(s)
    if cat_rows:
        from src.nlp.skill_dictionary_v2 import SKILL_CATEGORIES
        cat_df = (
            pd.Series([SKILL_CATEGORIES.get(s, "unknown") for s in cat_rows], dtype="object")
            .value_counts()
            .rename_axis("category")
            .reset_index(name="count")
        )
    else:
        cat_df = pd.DataFrame(columns=["category", "count"])
    cat_df.to_csv(Path(OUT_DIR) / "skill_categories_v2.csv", index=False, encoding="utf-8")

    print(f"[✓] All internships: {len(df)}")
    print(f"[✓] Tech internships kept: {len(tech_df)}")
    print(f"[✓] Saved: {out_all}")
    print(f"[✓] Saved: {out_tech}")
    print(f"[✓] Saved: {Path(OUT_DIR) / 'skill_frequency_v2.csv'}")
    print("\nTop 30 skills:\n")
    print(freq_df.head(30).to_string(index=False))

if __name__ == "__main__":
    main()
