"""
clean.py — reads raw parquet, outputs cleaned parquet
"""
import pandas as pd
import re
from pathlib import Path

RAW = Path("data/jobs_raw.parquet")
OUT = Path("data/jobs_clean.parquet")

def clean(df: pd.DataFrame) -> pd.DataFrame:
    # ── strip whitespace everywhere ──────────────────────────────────────────
    str_cols = df.select_dtypes("object").columns
    df[str_cols] = df[str_cols].apply(lambda c: c.str.strip())

    # ── deduplicate on detail_url ────────────────────────────────────────────
    df = df.drop_duplicates(subset="detail_url", keep="last")

    # ── normalize experience level ───────────────────────────────────────────
    level_map = {
        "junior": "Junior", "entry": "Junior",
        "intermediate": "Mid-Level", "mid": "Mid-Level",
        "senior": "Senior", "expert": "Senior/Expert",
        "intern": "Internship", "internship": "Internship",
    }
    df["experience_level"] = (
        df["experience_level"]
        .str.lower()
        .map(lambda v: next((level_map[k] for k in level_map if k in str(v)), v))
    )

    # ── normalize job_type ───────────────────────────────────────────────────
    df["work_mode"] = df["job_type"].str.extract(r"(Remote|Onsite|Hybrid)", expand=False).fillna("Unknown")
    df["contract_type"] = df["job_type"].str.extract(r"(Full Time|Part Time|Freelance|Contract)", expand=False).fillna("Unknown")

    # ── posted_date → datetime ───────────────────────────────────────────────
    df["posted_date"] = pd.to_datetime(df["posted_date"], errors="coerce")
    df["deadline"] = pd.to_datetime(df["deadline"], errors="coerce")
    df["scraped_at"] = pd.to_datetime(df["scraped_at"], errors="coerce")

    # ── week label for trend chart ───────────────────────────────────────────
    df["week"] = df["posted_date"].dt.to_period("W").astype(str)

    # ── salary: numeric extraction ───────────────────────────────────────────
    def parse_salary(raw):
        if pd.isna(raw):
            return None
        nums = re.findall(r"[\d,]+", str(raw))
        if nums:
            return int(nums[0].replace(",", ""))
        return None

    df["salary_etb"] = df["salary_raw"].apply(parse_salary)

    # ── skills: split & explode for skill frequency ──────────────────────────
    df["skills_list"] = df["skills"].fillna("").apply(
        lambda s: [x.strip() for x in re.split(r"[,\n]+", s) if x.strip()]
    )

    # ── industry: clean label ────────────────────────────────────────────────
    df["industry"] = df["industry"].fillna("Other").str.strip()

    # ── gender preference from applicants_needed ─────────────────────────────
    df["gender_pref"] = df["applicants_needed"].fillna("Both")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT, index=False)
    print(f"✓ Cleaned {len(df)} rows → {OUT}")
    return df

if __name__ == "__main__":
    df = pd.read_parquet(RAW)
    clean(df)
