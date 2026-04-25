"""
normalize.py — standardizes job titles and experience levels
Strategy: keyword taxonomy first, LLM fallback for unknowns, persistent cache.

Run order: clean.py → normalize.py → analyze.py → generate_report.py
"""
import json
import re
import time
import urllib.request
import urllib.error
from pathlib import Path

import pandas as pd

CLEAN      = Path("data/jobs_clean.parquet")
CACHE_FILE = Path("data/title_cache.json")

# ── LAYER 1: Experience level normalization ───────────────────────────────────
EXP_MAP = {
    # Junior / Entry
    "junior":      "Junior",
    "entry":       "Junior",
    "fresh":       "Junior",
    "trainee":     "Junior",
    "intern":      "Internship",
    "internship":  "Internship",
    # Mid
    "intermediate": "Mid-Level",
    "mid-level":    "Mid-Level",
    "mid level":    "Mid-Level",
    "associate":    "Mid-Level",
    # Senior / Expert
    "senior":      "Senior",
    "expert":      "Senior/Expert",
    "lead":        "Senior/Expert",
    "principal":   "Senior/Expert",
    "head":        "Senior/Expert",
    "director":    "Senior/Expert",
    "manager":     "Senior/Expert",
    "executive":   "Senior/Expert",
    "ceo":         "Senior/Expert",
    "cto":         "Senior/Expert",
    "cfo":         "Senior/Expert",
}

def normalize_experience(raw: str) -> str:
    if not raw or pd.isna(raw):
        return "Not Specified"
    v = str(raw).lower().strip()
    for key, label in EXP_MAP.items():
        if key in v:
            return label
    return str(raw).strip().title()


# ── LAYER 1: Job title taxonomy (keyword → category) ─────────────────────────
# Order matters — more specific phrases before generic ones.
TITLE_TAXONOMY = [
    # ── Tech & Engineering ────────────────────────────────────────────────────
    ("software engineer",        "Software Engineering"),
    ("software developer",       "Software Engineering"),
    ("full stack",               "Software Engineering"),
    ("backend developer",        "Software Engineering"),
    ("frontend developer",       "Software Engineering"),
    ("mobile developer",         "Software Engineering"),
    ("flutter",                  "Software Engineering"),
    ("android developer",        "Software Engineering"),
    ("ios developer",            "Software Engineering"),
    ("web developer",            "Software Engineering"),
    ("programmer",               "Software Engineering"),
    ("data engineer",            "Data & Analytics"),
    ("data analyst",             "Data & Analytics"),
    ("data scientist",           "Data & Analytics"),
    ("machine learning",         "Data & Analytics"),
    ("ai engineer",              "Data & Analytics"),
    ("business intelligence",    "Data & Analytics"),
    ("bi developer",             "Data & Analytics"),
    ("database",                 "Data & Analytics"),
    ("devops",                   "DevOps & Infrastructure"),
    ("sre",                      "DevOps & Infrastructure"),
    ("cloud engineer",           "DevOps & Infrastructure"),
    ("system administrator",     "DevOps & Infrastructure"),
    ("network engineer",         "DevOps & Infrastructure"),
    ("it support",               "IT Support"),
    ("it officer",               "IT Support"),
    ("technical support",        "IT Support"),
    ("helpdesk",                 "IT Support"),
    ("cybersecurity",            "Cybersecurity"),
    ("information security",     "Cybersecurity"),
    ("product manager",          "Product Management"),
    ("product owner",            "Product Management"),
    ("scrum master",             "Product Management"),
    ("ui designer",              "UI/UX Design"),
    ("ux designer",              "UI/UX Design"),
    ("ui/ux",                    "UI/UX Design"),
    ("user experience",          "UI/UX Design"),

    # ── Finance & Accounting ──────────────────────────────────────────────────
    ("accountant",               "Accounting & Finance"),
    ("accounting",               "Accounting & Finance"),
    ("finance officer",          "Accounting & Finance"),
    ("finance manager",          "Accounting & Finance"),
    ("financial analyst",        "Accounting & Finance"),
    ("financial controller",     "Accounting & Finance"),
    ("bookkeeper",               "Accounting & Finance"),
    ("cashier",                  "Accounting & Finance"),
    ("treasurer",                "Accounting & Finance"),
    ("auditor",                  "Accounting & Finance"),
    ("tax",                      "Accounting & Finance"),
    ("payroll",                  "Accounting & Finance"),
    ("budget",                   "Accounting & Finance"),

    # ── Sales & Marketing ─────────────────────────────────────────────────────
    ("sales",                    "Sales"),
    ("salesperson",              "Sales"),
    ("sales representative",     "Sales"),
    ("sales manager",            "Sales"),
    ("sales officer",            "Sales"),
    ("marketing",                "Marketing"),
    ("digital marketing",        "Marketing"),
    ("social media",             "Marketing"),
    ("seo",                      "Marketing"),
    ("content creator",          "Marketing"),
    ("brand",                    "Marketing"),
    ("market research",          "Marketing"),
    ("business development",     "Business Development"),
    ("business developer",       "Business Development"),
    ("bdr",                      "Business Development"),
    ("account manager",          "Business Development"),
    ("partnership",              "Business Development"),

    # ── HR & Admin ────────────────────────────────────────────────────────────
    ("human resource",           "Human Resources"),
    ("hr officer",               "Human Resources"),
    ("hr manager",               "Human Resources"),
    ("recruitment",              "Human Resources"),
    ("talent acquisition",       "Human Resources"),
    ("people operations",        "Human Resources"),
    ("administrative",           "Administration"),
    ("admin officer",            "Administration"),
    ("office manager",           "Administration"),
    ("secretary",                "Administration"),
    ("receptionist",             "Administration"),
    ("data entry",               "Administration"),
    ("executive assistant",      "Administration"),
    ("personal assistant",       "Administration"),

    # ── Engineering (non-software) ────────────────────────────────────────────
    ("civil engineer",           "Civil Engineering"),
    ("structural engineer",      "Civil Engineering"),
    ("quantity surveyor",        "Civil Engineering"),
    ("site engineer",            "Civil Engineering"),
    ("mechanical engineer",      "Mechanical Engineering"),
    ("electrical engineer",      "Electrical Engineering"),
    ("electrician",              "Electrical Engineering"),
    ("building electrician",     "Electrical Engineering"),
    ("chemical engineer",        "Chemical Engineering"),
    ("industrial engineer",      "Industrial Engineering"),
    ("engineering manager",      "Engineering Management"),

    # ── Healthcare ────────────────────────────────────────────────────────────
    ("doctor",                   "Healthcare"),
    ("physician",                "Healthcare"),
    ("nurse",                    "Healthcare"),
    ("pharmacist",               "Healthcare"),
    ("laboratory",               "Healthcare"),
    ("radiologist",              "Healthcare"),
    ("dentist",                  "Healthcare"),
    ("midwife",                  "Healthcare"),
    ("health officer",           "Healthcare"),
    ("clinical",                 "Healthcare"),
    ("medical",                  "Healthcare"),

    # ── Education & Training ──────────────────────────────────────────────────
    ("teacher",                  "Education & Training"),
    ("instructor",               "Education & Training"),
    ("trainer",                  "Education & Training"),
    ("lecturer",                 "Education & Training"),
    ("tutor",                    "Education & Training"),
    ("educator",                 "Education & Training"),
    ("academic",                 "Education & Training"),

    # ── Creative & Media ──────────────────────────────────────────────────────
    ("graphic design",           "Graphic Design"),
    ("graphic designer",         "Graphic Design"),
    ("illustrator",              "Graphic Design"),
    ("video editor",             "Video & Media Production"),
    ("videographer",             "Video & Media Production"),
    ("photographer",             "Video & Media Production"),
    ("motion graphic",           "Video & Media Production"),
    ("video producer",           "Video & Media Production"),
    ("media host",               "Video & Media Production"),
    ("content writer",           "Writing & Content"),
    ("copywriter",               "Writing & Content"),
    ("script writer",            "Writing & Content"),
    ("journalist",               "Writing & Content"),
    ("editor",                   "Writing & Content"),
    ("translator",               "Writing & Content"),
    ("voice over",               "Writing & Content"),

    # ── Operations & Supply Chain ─────────────────────────────────────────────
    ("operations",               "Operations & Logistics"),
    ("logistics",                "Operations & Logistics"),
    ("supply chain",             "Operations & Logistics"),
    ("procurement",              "Operations & Logistics"),
    ("warehouse",                "Operations & Logistics"),
    ("store keeper",             "Operations & Logistics"),
    ("storekeeper",              "Operations & Logistics"),
    ("inventory",                "Operations & Logistics"),
    ("driver",                   "Operations & Logistics"),
    ("delivery",                 "Operations & Logistics"),

    # ── Customer Service ──────────────────────────────────────────────────────
    ("customer service",         "Customer Service"),
    ("customer support",         "Customer Service"),
    ("call center",              "Customer Service"),
    ("helpline",                 "Customer Service"),

    # ── Legal ─────────────────────────────────────────────────────────────────
    ("lawyer",                   "Legal"),
    ("attorney",                 "Legal"),
    ("legal officer",            "Legal"),
    ("legal counsel",            "Legal"),
    ("paralegal",                "Legal"),
    ("compliance",               "Legal"),

    # ── Consulting ────────────────────────────────────────────────────────────
    ("consultant",               "Consulting"),
    ("advisory",                 "Consulting"),
    ("strategy",                 "Consulting"),
    ("analyst",                  "Consulting"),

    # ── Hospitality & Food ────────────────────────────────────────────────────
    ("chef",                     "Hospitality & Food Service"),
    ("cook",                     "Hospitality & Food Service"),
    ("waiter",                   "Hospitality & Food Service"),
    ("waitress",                 "Hospitality & Food Service"),
    ("barista",                  "Hospitality & Food Service"),
    ("hotel",                    "Hospitality & Food Service"),
    ("restaurant",               "Hospitality & Food Service"),
    ("hospitality",              "Hospitality & Food Service"),
    ("መስተንግዶ",                   "Hospitality & Food Service"),

    # ── Construction ─────────────────────────────────────────────────────────
    ("construction",             "Construction"),
    ("architect",                "Architecture"),
    ("interior design",          "Architecture"),

    # ── Agriculture ───────────────────────────────────────────────────────────
    ("agronomist",               "Agriculture"),
    ("agriculture",              "Agriculture"),
    ("farm",                     "Agriculture"),
    ("veterinary",               "Agriculture"),
]

def keyword_classify(title: str) -> str | None:
    """Return category if any keyword matches, else None."""
    t = title.lower().strip()
    for keyword, category in TITLE_TAXONOMY:
        if keyword in t:
            return category
    return None


# ── LAYER 2: LLM fallback via Anthropic API ───────────────────────────────────
CATEGORIES = sorted(set(v for _, v in TITLE_TAXONOMY))

SYSTEM_PROMPT = f"""You are a job title classifier for the Ethiopian job market.
Given a job title, return ONLY the single most appropriate category from this list:
{json.dumps(CATEGORIES, indent=2)}

Rules:
- Return exactly one category string, nothing else.
- No explanation, no punctuation, no markdown.
- If truly unclear, return "Other".
"""

def llm_classify(title: str, api_key_env: str = "GEMINI_API_KEY") -> str:
    """Call Gemini API to classify a single title. Returns category string."""
    import os
    api_key = os.environ.get(api_key_env, "")
    if not api_key:
        return "Other"

    prompt = f"{SYSTEM_PROMPT}\n\nJob title: {title}"
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 30, "temperature": 0},
    }).encode("utf-8")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        print(f"  ⚠ API error for '{title}': {e}")
        return "Other"


# ── Main normalization logic ──────────────────────────────────────────────────
def normalize(df: pd.DataFrame) -> pd.DataFrame:

    # ── 1. Experience level ───────────────────────────────────────────────────
    df["experience_level"] = df["experience_level"].apply(normalize_experience)

    # ── 2. Load cache ─────────────────────────────────────────────────────────
    cache: dict[str, str] = {}
    if CACHE_FILE.exists():
        cache = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        print(f"  Loaded {len(cache)} cached title classifications")

    # ── 3. Classify titles ────────────────────────────────────────────────────
    unique_titles = df["title"].dropna().unique().tolist()
    print(f"  {len(unique_titles)} unique titles to classify")

    new_from_api = 0
    for title in unique_titles:
        if title in cache:
            continue  # already known — free

        # Try keyword taxonomy first
        category = keyword_classify(title)
        if category:
            cache[title] = category
        else:
            # LLM fallback — only for genuinely unknown titles
            print(f"  → API classify: '{title}'")
            cache[title] = llm_classify(title)
            new_from_api += 1
            time.sleep(0.15)  # gentle rate limiting

    # ── 4. Save updated cache ─────────────────────────────────────────────────
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"  Cache updated: {new_from_api} new API calls, {len(cache)} total entries")

    # ── 5. Apply to dataframe ─────────────────────────────────────────────────
    df["title_category"] = df["title"].map(cache).fillna("Other")

    df.to_parquet(CLEAN, index=False)
    print(f"✓ Normalization complete → {CLEAN}")
    return df


if __name__ == "__main__":
    df = pd.read_parquet(CLEAN)
    normalize(df)