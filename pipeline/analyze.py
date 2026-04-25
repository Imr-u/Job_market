"""
analyze.py — reads cleaned parquet, outputs analysis.json
"""
import pandas as pd
import json
from pathlib import Path
from collections import Counter

CLEAN = Path("data/jobs_clean.parquet")
OUT   = Path("data/analysis.json")

def analyze(df: pd.DataFrame) -> dict:
    result = {}

    # ── 1. Top industries (job posts per field) ──────────────────────────────
    industry_counts = df["industry"].value_counts()
    result["industry"] = {
        "labels": industry_counts.index.tolist(),
        "values": industry_counts.values.tolist(),
        "top3":   industry_counts.head(3).index.tolist(),
    }

    # ── 2. Jobs per week ─────────────────────────────────────────────────────
    weekly = (
        df.groupby("week")["detail_url"]
        .count()
        .reset_index()
        .rename(columns={"detail_url": "count"})
        .sort_values("week")
    )
    result["weekly"] = {
        "labels": weekly["week"].tolist(),
        "values": weekly["count"].tolist(),
    }

    # ── 3. Experience level distribution ─────────────────────────────────────
    exp = df["experience_level"].value_counts()
    result["experience"] = {
        "labels": exp.index.tolist(),
        "values": exp.values.tolist(),
    }

    # ── 4. Work mode breakdown ───────────────────────────────────────────────
    mode = df["work_mode"].value_counts()
    result["work_mode"] = {
        "labels": mode.index.tolist(),
        "values": mode.values.tolist(),
    }

    # ── 5. Contract type ──────────────────────────────────────────────────────
    ct = df["contract_type"].value_counts()
    result["contract_type"] = {
        "labels": ct.index.tolist(),
        "values": ct.values.tolist(),
    }

    # ── 6. Top 15 in-demand skills ────────────────────────────────────────────
    all_skills = [skill for lst in df["skills_list"] for skill in lst if skill]
    skill_freq = Counter(all_skills).most_common(15)
    result["skills"] = {
        "labels": [s[0] for s in skill_freq],
        "values": [s[1] for s in skill_freq],
    }

    # ── 7. Education requirement distribution ────────────────────────────────
    edu = df["education_qualification"].fillna("Not Specified").value_counts()
    result["education"] = {
        "labels": edu.index.tolist(),
        "values": edu.values.tolist(),
    }

    # ── 8. Gender preference ─────────────────────────────────────────────────
    gender = df["gender_pref"].value_counts()
    result["gender"] = {
        "labels": gender.index.tolist(),
        "values": gender.values.tolist(),
    }

    # ── 9. Salary stats (ETB, where available) ───────────────────────────────
    sal = df["salary_etb"].dropna()
    if len(sal) > 0:
        result["salary"] = {
            "min":    int(sal.min()),
            "max":    int(sal.max()),
            "median": int(sal.median()),
            "mean":   int(sal.mean()),
            "period_breakdown": df[df["salary_etb"].notna()]["salary_period"]
                .value_counts().to_dict(),
        }
    else:
        result["salary"] = None

    # ── 10. Top hiring companies ──────────────────────────────────────────────
    # Filter out "Private Client" since it's a placeholder
    companies = (
        df[~df["company"].str.contains("Private Client", case=False, na=False)]
        ["company"].value_counts().head(10)
    )
    result["companies"] = {
        "labels": companies.index.tolist(),
        "values": companies.values.tolist(),
    }

    # ── 11. KPI summary ───────────────────────────────────────────────────────
    result["kpi"] = {
        "total_jobs":        int(len(df)),
        "total_companies":   int(df["company"].nunique()),
        "total_industries":  int(df["industry"].nunique()),
        "jobs_with_salary":  int(df["salary_etb"].notna().sum()),
        "remote_jobs":       int((df["work_mode"] == "Remote").sum()),
        "last_updated":      df["scraped_at"].max().isoformat() if not df["scraped_at"].isna().all() else "N/A",
        "date_range_start":  df["posted_date"].min().strftime("%b %d, %Y") if not df["posted_date"].isna().all() else "N/A",
        "date_range_end":    df["posted_date"].max().strftime("%b %d, %Y") if not df["posted_date"].isna().all() else "N/A",
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"✓ Analysis written → {OUT}")
    return result

if __name__ == "__main__":
    df = pd.read_parquet(CLEAN)
    analyze(df)
