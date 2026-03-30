# src/nlp/extract_skills.py

import re
from typing import List, Dict
from .skill_dictionary import TECH_SKILLS, SOFT_SKILLS

def _normalize(text: str) -> str:
    text = (text or "").lower()
    # keep basic symbols used in skills (c++, c#, node.js)
    text = re.sub(r"[^a-z0-9\+\#\.\s/]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def _compile_patterns(skills: List[str]) -> Dict[str, re.Pattern]:
    patterns = {}
    for s in skills:
        # word boundary-ish; allow dots and plus in skill names
        escaped = re.escape(s)
        pat = re.compile(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", re.I)
        patterns[s] = pat
    return patterns

TECH_PATTERNS = _compile_patterns(TECH_SKILLS)
SOFT_PATTERNS = _compile_patterns(SOFT_SKILLS)

def extract_skills(text: str) -> dict:
    t = _normalize(text)
    tech_found = []
    soft_found = []

    for skill, pat in TECH_PATTERNS.items():
        if pat.search(t):
            tech_found.append(skill)

    for skill, pat in SOFT_PATTERNS.items():
        if pat.search(t):
            soft_found.append(skill)

    # de-dup and sort for consistency
    tech_found = sorted(set(tech_found))
    soft_found = sorted(set(soft_found))

    return {
        "tech_skills": tech_found,
        "soft_skills": soft_found,
        "all_skills": sorted(set(tech_found + soft_found))
    }