import os
import re
import pandas as pd

IN_CSV = "data/processed/internships_with_skills.csv"
OUT_CSV = "data/processed/tech_internships.csv"

# Tech keywords for filtering
TECH_TITLE_PAT = re.compile(
    r"\b(software|developer|it\b|data|engineer|system|network|cloud|cyber|web|mobile|ai|ml|machine learning|analytics)\b",
    re.I
)

# Also check OCR text for safety
TECH_TEXT_PAT = re.compile(
    r"\b(python|java|sql|react|node|aws|azure|docker|git|html|css|javascript|c\+\+|c#|php|networking|cybersecurity)\b",
    re.I
)

def is_tech(row):
    title = str(row.get("title", ""))
    ocr_text = str(row.get("ocr_text", ""))

    if TECH_TITLE_PAT.search(title):
        return True
    if TECH_TEXT_PAT.search(ocr_text):
        return True
    return False

def main():
    os.makedirs("data/processed", exist_ok=True)
    df = pd.read_csv(IN_CSV)

    df["is_tech"] = df.apply(is_tech, axis=1)
    tech_df = df[df["is_tech"]].copy()

    tech_df.to_csv(OUT_CSV, index=False)

    print(f"[✓] Tech internships: {len(tech_df)}")
    print(f"Saved → {OUT_CSV}")

if __name__ == "__main__":
    main()