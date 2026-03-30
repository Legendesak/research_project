# Skill extraction pipeline v2

This pipeline reruns your internship skill extraction with:
- stronger OCR text normalization
- bigger skill dictionary with aliases
- exact matching first
- controlled RapidFuzz matching for OCR noise
- stricter tech internship filtering

## Expected input
Place your CSV file at one of these paths:
- `topjobs_internships.csv` in the project root, or
- edit `IN_CSV` inside `rerun_pipeline_v2.py`

The CSV should contain:
- `title`
- one OCR text column such as `ocr_text`, `ocr_text_raw`, or any column containing `ocr`

## Run
```bash
pip install -r requirements.txt
python rerun_pipeline_v2.py
```

## Outputs
Generated inside `output/`:
- `internships_with_skills_v2.csv`
- `tech_internships_v2.csv`
- `skill_frequency_v2.csv`
- `skill_categories_v2.csv`

## Methodology
1. Read internship CSV
2. Detect OCR text column
3. Normalize OCR noise
4. Extract skills using:
   - alias phrase replacement
   - exact regex matching
   - controlled fuzzy matching for longer terms only
5. Score each row for "techness"
6. Keep only stronger tech internships
7. Build frequency tables
