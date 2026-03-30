def detect_script(text: str) -> str:
    t = text or ""
    has_si = any('\u0D80' <= ch <= '\u0DFF' for ch in t)  # Sinhala block
    has_ta = any('\u0B80' <= ch <= '\u0BFF' for ch in t)  # Tamil block
    has_en = any(('a' <= ch.lower() <= 'z') for ch in t)

    if has_si and has_ta:
        return "mixed_si_ta"
    if has_si and has_en:
        return "mixed_si_en"
    if has_ta and has_en:
        return "mixed_ta_en"
    if has_si:
        return "si"
    if has_ta:
        return "ta"
    if has_en:
        return "en"
    return "unknown"