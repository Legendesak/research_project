import pandas as pd

FILES = [
    "mitesp_jobs_detailed.csv",
    "wso2_jobs_detailed.csv",
]

def main():
    dfs = []
    for f in FILES:
        try:
            df = pd.read_csv(f)
            if not df.empty:
                dfs.append(df)
        except Exception as e:
            print(f"Skipping {f}: {e}")

    if not dfs:
        print("No source files found.")
        return

    merged = pd.concat(dfs, ignore_index=True)
    merged.drop_duplicates(subset=["title", "company", "ad_url"], inplace=True)
    merged.to_csv("company_internships_detailed.csv", index=False, encoding="utf-8")
    print(f"[✓] Saved {len(merged)} rows -> company_internships_detailed.csv")

if __name__ == "__main__":
    main()