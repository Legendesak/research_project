import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def skills_to_text(skills: list[str]) -> str:
    return " ".join(skills)


def build_similarity_model(df: pd.DataFrame):
    internship_docs = df["tech_skills_list"].apply(skills_to_text).tolist()

    vectorizer = CountVectorizer(token_pattern=r"(?u)\b[\w\.\+#/]+\b")
    internship_matrix = vectorizer.fit_transform(internship_docs)

    return vectorizer, internship_matrix


def match_student_profile(
    student_skills: list[str],
    df: pd.DataFrame,
    vectorizer,
    internship_matrix,
    top_n: int = 10
) -> pd.DataFrame:
    student_doc = skills_to_text([s.lower().strip() for s in student_skills if s.strip()])
    student_vector = vectorizer.transform([student_doc])

    similarity_scores = cosine_similarity(student_vector, internship_matrix).flatten()

    results = df.copy()
    results["similarity"] = similarity_scores

    matched_skills = []
    missing_skills = []

    student_skill_set = set([s.lower().strip() for s in student_skills])

    for internship_skills in results["tech_skills_list"]:
        internship_set = set(internship_skills)
        matched = sorted(student_skill_set.intersection(internship_set))
        missing = sorted(internship_set.difference(student_skill_set))

        matched_skills.append(", ".join(matched))
        missing_skills.append(", ".join(missing))

    results["matched_skills"] = matched_skills
    results["missing_skills"] = missing_skills
    results["match_percentage"] = (results["similarity"] * 100).round(2)

    results = results.sort_values(by="similarity", ascending=False)

    return results.head(top_n)
