import pandas as pd


def parse_skills(skill_text: str) -> list[str]:
    if pd.isna(skill_text) or not str(skill_text).strip():
        return []
    return [s.strip().lower() for s in str(skill_text).split(",") if s.strip()]


def load_internships(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)

    # normalize expected columns
    expected_cols = ["title", "company", "town", "location", "tech_skills", "ad_url", "ocr_text"]
    for col in expected_cols:
        if col not in df.columns:
            df[col] = ""

    # if town missing but location exists
    if "town" in df.columns and df["town"].fillna("").eq("").all() and "location" in df.columns:
        df["town"] = df["location"]

    df["tech_skills_list"] = df["tech_skills"].apply(parse_skills)

    # remove rows with no useful skills
    df = df[df["tech_skills_list"].apply(len) > 0].copy()

    df.reset_index(drop=True, inplace=True)
    return df


def get_all_skills(df: pd.DataFrame) -> list[str]:
    skills = set()
    for row_skills in df["tech_skills_list"]:
        skills.update(row_skills)
    return sorted(skills)