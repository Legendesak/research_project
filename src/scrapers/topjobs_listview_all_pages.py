import os, re, json, time, random
from datetime import datetime, timezone
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

BASE_URL = "https://www.topjobs.lk"
OUT_RAW = "data/raw/topjobs_ads_listview"
OUT_IMG = "data/raw/topjobs_ads_listview/images"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/121.0 Safari/537.36"
}

# Pagination base you provided
LIST_BASE = ("https://www.topjobs.lk/applicant/vacancybyfunctionalarea.jsp"
             "?FA=&jst=OPEN&sQut=&txtKeyWord=&chkGovt=&chkParttime=&chkWalkin=&chkNGO=&pageNo={page}")

def safe_mkdir(p): os.makedirs(p, exist_ok=True)
def polite_sleep(): time.sleep(random.uniform(1.0, 2.2))
def abs_url(u: str) -> str: return urljoin(BASE_URL, u)

def get_soup(url: str) -> BeautifulSoup:
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return BeautifulSoup(r.text, "lxml")

def parse_date_text(s: str) -> str | None:
    """
    Input like: 'Fri Feb 27 2026' -> '2026-02-27' (best-effort)
    """
    s = (s or "").strip()
    if not s:
        return None
    # quick parse using datetime.strptime patterns
    try:
        dt = datetime.strptime(s, "%a %b %d %Y")
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return s  # fallback: keep original if unexpected format

def build_ad_url(ac: str, jc: str, ec: str) -> str:
    # You provided this pattern
    return (f"{BASE_URL}/employer/JobAdvertismentServlet?"
            f"rid=0&ac={ac}&jc={jc}&ec={ec}&pg=applicant/vacancybyfunctionalarea.jsp")

def extract_poster_image_url_from_ad(ad_url: str) -> str | None:
    """
    Many TopJobs ad pages show poster image inside HTML.
    We'll find image src containing '/logo/' or common ad image patterns.
    """
    soup = get_soup(ad_url)
    img = soup.select_one("img[src*='/logo/']") or soup.select_one("img")
    if not img:
        return None
    src = (img.get("src") or "").strip()
    if not src:
        return None
    return abs_url(src)


def parse_list_page(page_no: int) -> list[dict]:
    url = LIST_BASE.format(page=page_no)
    soup = get_soup(url)

    ads = []
    # table rows look like: <tr id="tr0" onclick="createAlert('0','DEFZZZ','0001474037','DEFZZZ',...)">
    for tr in soup.select("tr[id^='tr']"):
        onclick = tr.get("onclick", "")
        if "createAlert" not in onclick:
            continue

        # Extract ac, jc, ec from onclick args
        # createAlert('0','DEFZZZ','0001474037','DEFZZZ','token')
        m = re.search(r"createAlert\('(\d+)','([^']+)','([^']+)','([^']+)'", onclick)
        if not m:
            continue

        index = m.group(1)
        ac = m.group(2)
        jc = m.group(3)
        ec = m.group(4)

        tds = tr.find_all("td")
        if len(tds) < 7:
            continue

        job_ref_no = tds[1].get_text(strip=True) or None

        # title + employer inside td[2]
        title_el = tds[2].select_one("h2 span")
        employer_el = tds[2].select_one("h1")
        title = title_el.get_text(strip=True) if title_el else None
        employer = employer_el.get_text(strip=True) if employer_el else None

        short_desc = tds[3].get_text(" ", strip=True) or None
        opening_date_txt = tds[4].get_text(" ", strip=True)
        closing_date_txt = tds[5].get_text(" ", strip=True)
        town = tds[6].get_text(" ", strip=True) or None

        opening_date = parse_date_text(opening_date_txt)
        closing_date = parse_date_text(closing_date_txt)

        ad_url = build_ad_url(ac=ac, jc=jc, ec=ec)
        ad_id = f"topjobs_{job_ref_no}" if job_ref_no else f"topjobs_{jc}"

        ads.append({
            "ad_id": ad_id,
            "source": "TopJobs",
            "page_no": page_no,
            "list_page_url": url,
            "ad_url": ad_url,
            "ac": ac,
            "jc": jc,
            "ec": ec,
            "job_ref_no": job_ref_no,
            "title": title,
            "company": employer,
            "town": town,
            "opening_date": opening_date,
            "closing_date": closing_date,
            "short_description": short_desc,
        })

    return ads

def save_raw(ad: dict):
    safe_mkdir(OUT_RAW)
    path = os.path.join(OUT_RAW, f"{ad['ad_id']}.json")
    if os.path.exists(path):
        return False
    with open(path, "w", encoding="utf-8") as f:
        json.dump(ad, f, ensure_ascii=False, indent=2)
    return True

def run(max_pages: int = 20, fetch_poster_url: bool = True, download_images: bool = False):
    safe_mkdir(OUT_RAW)
    safe_mkdir(OUT_IMG)

    seen = set()
    total_new = 0

    for page in range(1, max_pages + 1):
        ads = parse_list_page(page)
        if not ads:
            print(f"[i] Page {page}: no ads found → stopping.")
            break

        new_ads = []
        for ad in ads:
            key = ad.get("job_ref_no") or ad["ad_id"]
            if key in seen:
                continue
            seen.add(key)
            new_ads.append(ad)

        print(f"[+] Page {page}: found={len(ads)} new={len(new_ads)} total_unique={len(seen)}")

        if not new_ads:
            print("[i] No new ads detected → stopping.")
            break

        # Optionally fetch poster URLs (and download image later)
        for ad in tqdm(new_ads, desc=f"Poster fetch p{page}"):
            try:
                ad["scraped_at"] = datetime.now(timezone.utc).isoformat()
                if fetch_poster_url:
                    poster = extract_poster_image_url_from_ad(ad["ad_url"])
                    ad["poster_image_url"] = poster

                    if poster and download_images:
                        ext = os.path.splitext(poster.split("?")[0])[1] or ".png"
                        img_path = os.path.join(OUT_IMG, f"{ad['ad_id']}{ext}")
                        ad["poster_image_file"] = img_path

                        if not os.path.exists(img_path):
                            r = requests.get(poster, headers=HEADERS, timeout=60)
                            r.raise_for_status()
                            with open(img_path, "wb") as f:
                                f.write(r.content)
                save_raw(ad)
                total_new += 1
            except Exception as e:
                ad["error"] = str(e)
                save_raw(ad)
            polite_sleep()

        polite_sleep()

    print(f"[✓] Done. Saved {total_new} new ads into {OUT_RAW}")

if __name__ == "__main__":
    # Since you said there are 6 pages, set max_pages=6 (or leave 20 to auto-stop)
    run(max_pages=20, fetch_poster_url=True, download_images=False)