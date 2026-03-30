import re
from collections import defaultdict
from rapidfuzz import fuzz
from .skill_dictionary_v2 import SKILL_CATEGORIES, SKILL_ALIASES, WEAK_OR_AMBIGUOUS_TERMS
from .text_normalizer_v2 import normalize_text, make_ngrams

CANONICAL_SKILLS = sorted(SKILL_CATEGORIES.keys(), key=len, reverse=True)

def _exact_match_skills(text: str):
    found = set()
    for skill in CANONICAL_SKILLS:
        if skill in WEAK_OR_AMBIGUOUS_TERMS:
            # handle these more carefully later
            continue
        if re.search(rf"(?<![a-z0-9]){re.escape(skill)}(?![a-z0-9])", text):
            found.add(skill)
    return found

def _careful_short_skill_match(text: str):
    found = set()

    # c++ and c# are safe
    for skill in ["c++", "c#"]:
        if re.search(rf"(?<![a-z0-9]){re.escape(skill)}(?![a-z0-9])", text):
            found.add(skill)

    # standalone c must appear in programming-like context
    if re.search(r"(?<![a-z0-9])c(?![a-z0-9])", text):
        if re.search(r"(programming|language|developer|developer intern|software|coding|c\+\+|c#)", text):
            found.add("c")

    # go only if golang or a clear tech phrase exists
    if re.search(r"(?<![a-z0-9])golang(?![a-z0-9])", text):
        found.add("go")
    elif re.search(r"(?<![a-z0-9])go(?![a-z0-9])", text) and re.search(r"(developer|backend|microservices|api|programming|language)", text):
        found.add("go")

    # r only if data context exists
    if re.search(r"(?<![a-z0-9])r(?![a-z0-9])", text) and re.search(r"(statistics|data|analytics|machine learning|data science)", text):
        found.add("r")

    # qa only if exact context
    if re.search(r"(?<![a-z0-9])qa(?![a-z0-9])", text) or "quality assurance" in text:
        found.add("qa")

    # excel only if exact
    if re.search(r"(?<![a-z0-9])excel(?![a-z0-9])", text):
        found.add("excel")

    if re.search(r"(?<![a-z0-9])database(?![a-z0-9])", text):
        found.add("database")

    if re.search(r"(?<![a-z0-9])testing(?![a-z0-9])", text):
        found.add("testing")

    return found

def _fuzzy_match_skills(text: str):
    found = set()
    grams = make_ngrams(text, n_values=(1,2,3))
    # only fuzzy match longer non-ambiguous skills
    candidate_skills = [
    s for s in CANONICAL_SKILLS
    if len(s) >= 6
    and s not in WEAK_OR_AMBIGUOUS_TERMS
    and s not in {"testing", "database", "excel", "networking"}
]

    for gram in grams:
        if len(gram) < 5:
            continue
        for skill in candidate_skills:
            # avoid expensive comparisons when length is wildly different
            if abs(len(skill) - len(gram)) > 3:
                continue
            score = fuzz.ratio(skill, gram)
            if score >= 94:
                found.add(skill)
    return found

def extract_skills(text: str):
    clean = normalize_text(text)

    exact = _exact_match_skills(clean)
    careful = _careful_short_skill_match(clean)
    fuzzy = _fuzzy_match_skills(clean)

    all_found = sorted(exact | careful | fuzzy)
    tech = []
    soft = []
    categories = defaultdict(list)

    for skill in all_found:
        cat = SKILL_CATEGORIES.get(skill)
        categories[cat].append(skill)
        if cat == "soft":
            soft.append(skill)
        else:
            tech.append(skill)

    return {
        "normalized_text": clean,
        "tech_skills": sorted(set(tech)),
        "soft_skills": sorted(set(soft)),
        "all_skills": sorted(set(all_found)),
        "categories": {k: sorted(set(v)) for k, v in categories.items() if k}
    }
