import re
import time
import random
from urllib.parse import urljoin

import requests
import pandas as pd
from bs4 import BeautifulSoup

BASE_URL = "https://www.careers-page.com"
LIST_URL = "https://www.careers-page.com/mitesp"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

KEYWORDS = [
    "intern", "internship", "trainee", "graduate", "fresh graduate",
    "associate trainee", "entry level", "fresh"
]


def polite_sleep():
    time.sleep(random.uniform(0.4, 0.9))


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def is_internship(title: str) -> bool:
    t = (title or "").lower()
    return any(k in t for k in KEYWORDS)


def extract_description_from_detail(detail_url: str) -> str:
    """
    Optional detail-page scrape.
    If detail page is not easily reachable, returns empty string.
    """
    try:
        r = requests.get(detail_url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")

        selectors = [
            ".job-description",
            ".description",
            ".content",
            "main",
            "article",
            "body",
        ]

        for sel in selectors:
            node = soup.select_one(sel)
            if node:
                text = clean_text(node.get_text(" ", strip=True))
                if len(text) > 120:
                    return text
    except Exception:
        pass

    return ""


def scrape_mitesp() -> pd.DataFrame:
    r = requests.get(LIST_URL, headers=HEADERS, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")

    jobs = []
    seen = set()

    # This page renders each opening as:
    # ##### Title
    # Location
    # Department
    # Apply
    #
    # So parse all headings first, then read nearby text.
    headings = soup.find_all(["h5", "h4", "h3"])
    print(f"[i] Headings found: {len(headings)}")

    for h in headings:
        title = clean_text(h.get_text(" ", strip=True))

        if not title:
            continue
        if title.lower() in {
            "our openings", "16 open positions", "[[ count ]] result", "[[ count ]] results"
        }:
            continue
        if not is_internship(title):
            continue

        # collect nearby sibling text until Apply / next heading
        block_lines = []
        for sib in h.next_siblings:
            # stop when next heading starts
            if getattr(sib, "name", None) in {"h3", "h4", "h5"}:
                break

            text = ""
            if hasattr(sib, "get_text"):
                text = clean_text(sib.get_text(" ", strip=True))
            else:
                text = clean_text(str(sib))

            if not text:
                continue

            # split large chunks
            for part in re.split(r"\n+", text):
                part = clean_text(part)
                if part:
                    block_lines.append(part)

            # stop after Apply appears
            if "apply" in text.lower():
                break

        # remove obvious noise
        cleaned_lines = []
        for line in block_lines:
            low = line.lower()
            if low in {"apply", "view openings", "search"}:
                continue
            if line == title:
                continue
            cleaned_lines.append(line)

        # infer location and department
        location = ""
        department = ""

        for line in cleaned_lines:
            low = line.lower()
            if "sri lanka" in low or "colombo" in low:
                location = line
                break

        for line in cleaned_lines:
            if line != location and len(line) <= 80:
                department = line
                break

        # try to find nearby apply link
        detail_url = LIST_URL
        apply_link = None

        parent = h.parent
        if parent:
            for a in parent.find_all("a", href=True):
                txt = clean_text(a.get_text(" ", strip=True)).lower()
                if "apply" in txt:
                    apply_link = a
                    break

        if not apply_link:
            for a in h.find_all_next("a", href=True, limit=8):
                txt = clean_text(a.get_text(" ", strip=True)).lower()
                if "apply" in txt:
                    apply_link = a
                    break

        if apply_link:
            detail_url = urljoin(BASE_URL, apply_link.get("href", ""))

        key = (title.lower(), detail_url)
        if key in seen:
            continue
        seen.add(key)

        description_text = extract_description_from_detail(detail_url)

        jobs.append({
            "source": "MIT ESP",
            "title": title,
            "company": "MIT ESP",
            "location": location or "Colombo, Sri Lanka",
            "department": department,
            "employment_type": "Internship" if "intern" in title.lower() else "",
            "ad_url": detail_url,
            "description_text": description_text,
            "raw_text": f"{title} {location} {department} {description_text}".strip(),
        })

        polite_sleep()

    columns = [
        "source", "title", "company", "location",
        "department", "employment_type", "ad_url",
        "description_text", "raw_text"
    ]

    return pd.DataFrame(jobs, columns=columns).drop_duplicates(
        subset=["title", "company", "location"]
    )


if __name__ == "__main__":
    df = scrape_mitesp()
    df.to_csv("mitesp_jobs_detailed.csv", index=False, encoding="utf-8")

    print(f"[✓] Rows scraped: {len(df)}")
    if not df.empty:
        print(df[["title", "location", "department"]].to_string(index=False))
    else:
        print("[!] No internship rows found.")