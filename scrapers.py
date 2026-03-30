import os, re, json, time, random, hashlib
from datetime import datetime
from urllib.parse import urljoin

import requests
import bs4
import tqdm

# OCR (optional but recommended)
import pytesseract
import cv2
from PIL import Image


LIST_URL = "https://www.topjobs.lk/do.landing?CO=FA&FA=AV&SV=y&SV=y&SV=y&SV=y&SV=y&SV=y&SV=y&SV=y&SV=y&SV=y&SV=y&SV=y&SV=y"
BASE_URL = "https://www.topjobs.lk"

OUT_RAW = "data/raw/topjobs_ads"
OUT_IMG = "data/raw/topjobs_ads/images"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/121.0 Safari/537.36"
}

def safe_mkdir(p): os.makedirs(p, exist_ok=True)
def polite_sleep(): time.sleep(random.uniform(1.2, 2.6))

def sha_id(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]

def get_soup(url: str) -> bs4.BeautifulSoup:
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return bs4.BeautifulSoup(r.text, "lxml")

def abs_url(href: str) -> str:
    return urljoin(BASE_URL, href)

def parse_list_page(list_url: str) -> list[dict]:
    soup = get_soup(list_url)
    ads = []

    # Each ad container: div.job-ad.live-search-list
    for ad_div in soup.select("div.job-ad.live-search-list"):
        a = ad_div.select_one("a.openAd.job-link.job-title")
        if not a:
            continue

        title = a.get_text(strip=True) or None
        ad_url = abs_url(a.get("href", "").strip())
        jc = a.get("id", "").strip()  # e.g. 0001473628

        company_el = ad_div.select_one("label.lbl-job-owner a.job-owner")
        company = company_el.get_text(strip=True) if company_el else None

        loc_el = ad_div.select_one("label.job-location span.location-area")
        location = loc_el.get_text(" ", strip=True) if loc_el else None

        # dates
        cd = ad_div.select_one("span.closing-date")
        start_date = cd.get("data-startingdate") if cd else None
        end_date = cd.get("data-closingdate") if cd else None

        ref_el = ad_div.select_one("span.job-ref-value")
        job_ref_no = ref_el.get_text(strip=True) if ref_el else None

        ad_id = f"topjobs_{job_ref_no}" if job_ref_no else f"topjobs_{sha_id(ad_url)}"

        ads.append({
            "ad_id": ad_id,
            "source": "TopJobs",
            "list_page_url": list_url,
            "ad_url": ad_url,
            "jc": jc or None,
            "title": title,
            "company": company,
            "location": location,
            "start_date": start_date,
            "end_date": end_date,
            "job_ref_no": job_ref_no,
        })

    return ads

def extract_poster_image_url(ad_url: str) -> str | None:
    soup = get_soup(ad_url)

    # Your exact container: div#remark img
    img = soup.select_one("#remark img")
    if not img:
        # fallback in case layout changes
        img = soup.select_one("img.shrunk-image") or soup.select_one("img[src*='/logo/']")

    if not img:
        return None

    return abs_url(img.get("src", "").strip())

def download_image(img_url: str, out_path: str):
    r = requests.get(img_url, headers=HEADERS, timeout=60)
    r.raise_for_status()
    with open(out_path, "wb") as f:
        f.write(r.content)

def preprocess_for_ocr(img_path: str) -> str:
    """
    Improves OCR accuracy: grayscale + threshold.
    Saves a temp processed image and returns its path.
    """
    img = cv2.imread(img_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # adaptive threshold often helps poster scans
    thr = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                cv2.THRESH_BINARY, 31, 7)
    processed_path = img_path.replace(".png", "_proc.png").replace(".jpg", "_proc.jpg")
    cv2.imwrite(processed_path, thr)
    return processed_path

def ocr_image(img_path: str) -> str:
    processed = preprocess_for_ocr(img_path)
    text = pytesseract.image_to_string(Image.open(processed))
    return text

def save_raw_json(ad: dict):
    safe_mkdir(OUT_RAW)
    out = os.path.join(OUT_RAW, f"{ad['ad_id']}.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(ad, f, ensure_ascii=False, indent=2)

def run(max_ads: int = 200, do_ocr: bool = True):
    safe_mkdir(OUT_RAW)
    safe_mkdir(OUT_IMG)

    ads = parse_list_page(LIST_URL)
    print(f"[+] Found {len(ads)} ads on list page")

    ads = ads[:max_ads]
    for ad in tqdm.tqdm(ads, desc="Scraping ads"):
        try:
            # poster image url
            poster_url = extract_poster_image_url(ad["ad_url"])
            ad["poster_image_url"] = poster_url
            ad["scraped_at"] = datetime.utcnow().isoformat() + "Z"

            if poster_url:
                img_ext = os.path.splitext(poster_url.split("?")[0])[1] or ".png"
                img_path = os.path.join(OUT_IMG, f"{ad['ad_id']}{img_ext}")
                ad["poster_image_file"] = img_path

                # download if not exists
                if not os.path.exists(img_path):
                    download_image(poster_url, img_path)

                # OCR
                if do_ocr:
                    ad["ocr_text_raw"] = ocr_image(img_path)
                else:
                    ad["ocr_text_raw"] = None
            else:
                ad["poster_image_file"] = None
                ad["ocr_text_raw"] = None

            save_raw_json(ad)

        except Exception as e:
            ad["error"] = str(e)
            save_raw_json(ad)

        polite_sleep()

    print(f"[✓] Done. Saved raw JSON to {OUT_RAW}")

if __name__ == "__main__":
    run(max_ads=20, do_ocr=True)