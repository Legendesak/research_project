import os, json, re
import pandas as pd

RAW_DIR = "data/raw/topjobs_ads_listview"
OUT_CSV = "data/processed/topjobs_master.csv"

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"(\+?\d[\d\s\-()]{7,}\d)")

def extract_emails(text: str):
    return sorted(set(EMAIL_RE.findall(text or "")))

def extract_phones(text: str):
    raw = PHONE_RE.findall(text or "")
    cleaned = []
    for p in raw:
        p2 = re.sub(r"\s+", " ", p).strip()
        cleaned.append(p2)
    return sorted(set(cleaned))

def main():
    os.makedirs("data/processed", exist_ok=True)

    rows = []
    for fn in os.listdir(RAW_DIR):
        if not fn.endswith(".json"):
            continue
        path = os.path.join(RAW_DIR, fn)
        with open(path, "r", encoding="utf-8") as f:
            ad = json.load(f)

        ocr = ad.get("ocr_text_raw") or ""

        rows.append({
            "ad_id": ad.get("ad_id"),
            "title": ad.get("title"),
            "company": ad.get("company"),
            "town": ad.get("town"),
            "opening_date": ad.get("opening_date"),
            "closing_date": ad.get("closing_date"),
            "ad_url": ad.get("ad_url"),
            "vacancy_details_url": ad.get("vacancy_details_url"),
            "poster_image_file": ad.get("poster_image_file"),
            "emails": ", ".join(extract_emails(ocr)),
            "phones": ", ".join(extract_phones(ocr)),
            "ocr_text": ocr
        })

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False, encoding="utf-8")
    print(f"[✓] Saved {len(df)} rows → {OUT_CSV}")

if __name__ == "__main__":
    main()