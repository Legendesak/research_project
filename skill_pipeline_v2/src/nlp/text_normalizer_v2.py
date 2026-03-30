import re
from unidecode import unidecode
from .skill_dictionary_v2 import OCR_REPAIRS, SKILL_ALIASES

def normalize_text(text: str) -> str:
    text = text or ""
    text = text.replace("\u200b", " ").replace("\xa0", " ")
    text = unidecode(text)
    text = text.lower()

    # preserve important skill symbols
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9\+\#\./\-\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    # apply OCR-specific repairs
    for bad, good in OCR_REPAIRS.items():
        text = text.replace(bad, good)

    # alias phrase normalization
    # longer aliases first to avoid partial overwrites
    for alias in sorted(SKILL_ALIASES, key=len, reverse=True):
        canonical = SKILL_ALIASES[alias]
        text = re.sub(rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])", canonical, text)

    # normalize slash spacing
    text = text.replace("ui / ux", "ui/ux")
    text = re.sub(r"\s*/\s*", "/", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text

def make_ngrams(text: str, n_values=(1,2,3)):
    tokens = text.split()
    grams = []
    for n in n_values:
        for i in range(len(tokens)-n+1):
            grams.append(" ".join(tokens[i:i+n]))
    return grams
