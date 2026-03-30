import os, json, time, random
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

BASE_URL = "https://www.topjobs.lk"
RAW_DIR = "data/raw/topjobs_ads_listview"
IMG_DIR = "data/raw/topjobs_ads_listview/images"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/121.0 Safari/537.36"
}

def polite_sleep():
    time.sleep(random.uniform(0.8, 1.8))

def abs_url(u: str) -> str:
    return urljoin(BASE_URL, u)

def vacancy_details_url(ad: dict) -> str:
    ac = ad.get("ac")
    jc = ad.get("jc")
    ec = ad.get("ec")
    if not (ac and jc and ec):
        return ad.get("ad_url")
    return f"{BASE_URL}/vacancy?ac={ac}&jc={jc}&ec={ec}&pg=applicant/vacancyDetails.jsp"

def get_poster_url_from_vacancy_details(ad: dict) -> str | None:
    url = vacancy_details_url(ad)
    r = requests.get(url, headers=HEADERS, timeout=30, allow_redirects=True)
    r.raise_for_status()

    ctype = (r.headers.get("Content-Type") or "").lower()
    if ctype.startswith("image/"):
        return url

    soup = BeautifulSoup(r.text, "lxml")
    img = soup.select_one("#remark img")
    if not img:
        return None

    src = (img.get("src") or "").strip()
    if not src:
        return None

    return abs_url(src)

def download(url: str, path: str):
    r = requests.get(url, headers=HEADERS, timeout=60, allow_redirects=True)
    r.raise_for_status()
    with open(path, "wb") as f:
        f.write(r.content)

def main(limit: int | None = None, only_missing: bool = True):
    os.makedirs(IMG_DIR, exist_ok=True)

    files = [f for f in os.listdir(RAW_DIR) if f.endswith(".json")]
    if limit:
        files = files[:limit]

    for fn in tqdm(files, desc="Downloading posters"):
        path = os.path.join(RAW_DIR, fn)
        with open(path, "r", encoding="utf-8") as f:
            ad = json.load(f)

        if only_missing and ad.get("poster_image_file") and os.path.exists(ad["poster_image_file"]):
            continue

        try:
            # always compute vacancy details URL
            ad["vacancy_details_url"] = vacancy_details_url(ad)

            # overwrite poster url if only_missing=False
            poster_url = None if not only_missing else ad.get("poster_image_url")
            if not poster_url:
                poster_url = get_poster_url_from_vacancy_details(ad)
                ad["poster_image_url"] = poster_url

            if poster_url:
                ext = os.path.splitext(poster_url.split("?")[0])[1] or ".png"
                img_path = os.path.join(IMG_DIR, f"{ad['ad_id']}{ext}")
                download(poster_url, img_path)
                ad["poster_image_file"] = img_path

            with open(path, "w", encoding="utf-8") as fw:
                json.dump(ad, fw, ensure_ascii=False, indent=2)

        except Exception as e:
            ad["poster_error"] = str(e)
            with open(path, "w", encoding="utf-8") as fw:
                json.dump(ad, fw, ensure_ascii=False, indent=2)

        polite_sleep()

if __name__ == "__main__":
    main(limit=None, only_missing=False)