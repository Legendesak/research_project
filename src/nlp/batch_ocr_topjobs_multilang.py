import os, json, time, random
from PIL import Image
import pytesseract
import cv2
from tqdm import tqdm

RAW_DIR = "data/raw/topjobs_ads_listview"

def polite_sleep():
    time.sleep(random.uniform(0.2, 0.6))

def preprocess(img_path: str) -> str:
    img = cv2.imread(img_path)
    if img is None:
        raise ValueError(f"Cannot read image: {img_path}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    thr = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 7
    )
    out_path = img_path.rsplit(".", 1)[0] + "_proc.png"
    cv2.imwrite(out_path, thr)
    return out_path

def detect_script(text: str) -> str:
    t = text or ""
    has_si = any('\u0D80' <= ch <= '\u0DFF' for ch in t)  # Sinhala Unicode block
    has_ta = any('\u0B80' <= ch <= '\u0BFF' for ch in t)  # Tamil Unicode block
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

def ocr_with_lang(img_path: str, lang: str) -> str:
    proc = preprocess(img_path)
    return pytesseract.image_to_string(Image.open(proc), lang=lang, config="--psm 6")

def best_of(text_a: str, text_b: str) -> str:
    # Choose the text that is "more useful" (longer non-space chars)
    a = len((text_a or "").strip())
    b = len((text_b or "").strip())
    return text_b if b > a else text_a

def ocr_auto(img_path: str) -> tuple[str, str]:
    """
    1) OCR in English first (fast)
    2) If short/unreadable OR Sinhala/Tamil detected, retry with sin/tam combinations
    """
    text_eng = ocr_with_lang(img_path, "eng")
    script = detect_script(text_eng)

    # If English OCR already good enough, keep it
    if len(text_eng.strip()) >= 60 and script in ["en", "mixed_si_en", "mixed_ta_en"]:
        return text_eng, script

    # Retry Sinhala + English
    text = text_eng
    try:
        text_sin = ocr_with_lang(img_path, "sin+eng")
        text = best_of(text, text_sin)
    except Exception:
        pass

    # Retry Tamil + English
    try:
        text_tam = ocr_with_lang(img_path, "tam+eng")
        text = best_of(text, text_tam)
    except Exception:
        pass

    # If mixed posters, try all (slowest, last resort)
    if len(text.strip()) < 60:
        try:
            text_all = ocr_with_lang(img_path, "sin+tam+eng")
            text = best_of(text, text_all)
        except Exception:
            pass

    return text, detect_script(text)

def main(batch_size: int = 50, start_index: int = 0, only_missing: bool = True):
    files = sorted([f for f in os.listdir(RAW_DIR) if f.endswith(".json")])
    files = files[start_index:start_index + batch_size]
    print(f"OCR batch: {len(files)} files (start_index={start_index})")

    for fn in tqdm(files, desc="OCR"):
        path = os.path.join(RAW_DIR, fn)
        with open(path, "r", encoding="utf-8") as f:
            ad = json.load(f)

        if only_missing and ad.get("ocr_text_raw"):
            continue

        img_path = ad.get("poster_image_file")
        if not img_path or not os.path.exists(img_path):
            ad["ocr_error"] = "poster_image_file missing"
        else:
            try:
                text, lang_tag = ocr_auto(img_path)
                ad["ocr_text_raw"] = text
                ad["ocr_lang"] = lang_tag
                ad.pop("ocr_error", None)
            except Exception as e:
                ad["ocr_error"] = str(e)

        with open(path, "w", encoding="utf-8") as fw:
            json.dump(ad, fw, ensure_ascii=False, indent=2)

        polite_sleep()

    print("[✓] Batch complete.")

if __name__ == "__main__":
    # First batch
    main(batch_size=500, start_index=5000, only_missing=True)