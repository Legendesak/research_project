import os
import pandas as pd
from src.nlp.extract_skills import extract_skills

IN_CSV = "data/processed/topjobs_internships.csv"          # your uploaded file (keep it in project root OR adjust path)
OUT_CSV = "data/processed/internships_with_skills.csv"

def main():
    os.makedirs("data/processed", exist_ok=True)
    df = pd.read_csv(IN_CSV)

    # choose the best text column you have
    text_col = "ocr_text" if "ocr_text" in df.columns else None
    if text_col is None:
        # fallback: any column that contains OCR
        for c in df.columns:
            if "ocr" in c.lower():
                text_col = c
                break
    if text_col is None:
        raise ValueError("No OCR text column found in CSV.")

    tech_list = []
    soft_list = []
    all_list = []

    for t in df[text_col].fillna("").astype(str).tolist():
        res = extract_skills(t)
        tech_list.append(", ".join(res["tech_skills"]))
        soft_list.append(", ".join(res["soft_skills"]))
        all_list.append(", ".join(res["all_skills"]))

    df["tech_skills"] = tech_list
    df["soft_skills"] = soft_list
    df["skills_all"] = all_list

    df.to_csv(OUT_CSV, index=False, encoding="utf-8")
    print(f"[✓] Saved: {OUT_CSV} ({len(df)} rows)")

if __name__ == "__main__":
    main()