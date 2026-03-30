import re
import time
import random
from urllib.parse import urljoin

import requests
import pandas as pd
from bs4 import BeautifulSoup

BASE_URL = "https://wso2.com"
LIST_URL = "https://wso2.com/careers/"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

KEYWORDS = [
    "intern", "internship", "trainee", "graduate", "associate trainee", "entry level"
]


def polite_sleep():
    time.sleep(random.uniform(0.8, 1.6))


def is_internship(title: str) -> bool:
    t = (title or "").lower()
    return any(k in t for k in KEYWORDS)


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def extract_description_from_detail(detail_url: str) -> str:
    r = requests.get(detail_url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")

    candidates = [
        soup.select_one("main"),
        soup.select_one("article"),
        soup.select_one(".job-description"),
        soup.select_one(".content"),
    ]

    for node in candidates:
        if node:
            text = clean_text(node.get_text(" ", strip=True))
            if len(text) > 120:
                return text

    body = soup.body.get_text(" ", strip=True) if soup.body else ""
    return clean_text(body)


def scrape_wso2() -> pd.DataFrame:
    r = requests.get(LIST_URL, headers=HEADERS, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")

    jobs = []
    seen = set()

    # Strategy:
    # look for "Apply Now" links, then look back for nearby title/meta text
    all_links = soup.select("a[href]")

    for a in all_links:
        label = clean_text(a.get_text(" ", strip=True))
        href = (a.get("href") or "").strip()

        if "apply now" not in label.lower():
            continue

        detail_url = urljoin(BASE_URL, href)

        # try to locate nearby heading/title
        parent = a.parent
        block_text = clean_text(parent.get_text(" ", strip=True)) if parent else ""
        lines = [x.strip() for x in re.split(r"\s{2,}", block_text) if x.strip()]

        # fallback title from nearest previous heading
        title = ""
        for prev in a.find_all_previous(["h1", "h2", "h3", "h4"], limit=3):
            candidate = clean_text(prev.get_text(" ", strip=True))
            if candidate and candidate.lower() != "available positions":
                title = candidate
                break

        if not title:
            title = block_text[:120]

        if not is_internship(title):
            continue

        key = (title.lower(), detail_url)
        if key in seen:
            continue
        seen.add(key)

        # try to infer location / type from nearby text
        location = ""
        employment_type = ""
        nearby = clean_text(parent.get_text(" ", strip=True)) if parent else ""
        if "sri lanka" in nearby.lower():
            location = "Sri Lanka"
        if "full time" in nearby.lower():
            employment_type = "Full Time"
        elif "intern" in title.lower():
            employment_type = "Internship"

        try:
            description_text = extract_description_from_detail(detail_url)
        except Exception:
            description_text = ""

        jobs.append({
            "source": "WSO2",
            "title": title,
            "company": "WSO2",
            "location": location,
            "department": "",
            "employment_type": employment_type,
            "ad_url": detail_url,
            "description_text": description_text,
            "raw_text": f"{title} {description_text}".strip(),
        })

        polite_sleep()

    df = pd.DataFrame(jobs).drop_duplicates(subset=["title", "company", "ad_url"])
    return df


if __name__ == "__main__":
    df = scrape_wso2()
    df.to_csv("wso2_jobs_detailed.csv", index=False, encoding="utf-8")
    print(df[["title", "ad_url"]].head())
    print(f"[✓] Saved {len(df)} rows -> wso2_jobs_detailed.csv")