"""
clean.py — reads raw parquet, outputs cleaned parquet
"""
import pandas as pd
import re
from pathlib import Path

RAW = Path("data/jobs_raw.parquet")
OUT = Path("data/jobs_clean.parquet")

import re
import pandas as pd

TITLE_BUCKETS = [

    # ── Sales (all variants) ─────────────────────────────────────────────────
    ("Sales Manager",        ["sales manager", "sales supervisor", "sales team leader",
                               "sales lead", "sales supervisor", "shop manager",
                               "showroom manager", "sales and operation manager"]),

    ("Sales Representative", ["sales rep", "sales representative", "salesperson",
                               "sales person", "sales agent", "sales officer",
                               "sales executive", "sales consultant", "sales associate",
                               "sales specialist", "sales trainee", "sales staff",
                               "outdoor sales", "field sales", "b2b sales",
                               "door to door sales", "sales women", "sales man",
                               "sales girl", "female sales", "shop sales",
                               "store sales", "sales represntative", "sales represntative",
                               "sales represntative", "sales excutive", "sales consulrtant",
                               "sales represntative", "sales agent", "sales officer",
                               "product sales", "real estate sales", "realestate sales",
                               "ftth sales", "spare-parts sales", "directory sales",
                               "call sales", "junior sales", "senior sales",
                               "የሽያጭ ሰራተኛ", "ሽያጭ ሰራተኛ", "የሽያጭ ሠራተኛ",
                               "የሽያጭ ባለሙያ", "ሲኒየር የሽያጭ", "sales",
                               "growth associate", "merchant acquisition",
                               "outsdie sales", "shop clerk", "shop keeper",
                               "store clerk", "sales and marketing"]),

    # ── Accounting & Finance ─────────────────────────────────────────────────
    ("Senior Accountant",    ["senior accountant", "senior cost accountant",
                               "ሲኒየር አካውንታንት"]),

    ("Accountant",           ["accountant", "junior accountant", "accounting officer",
                               "accounting clerk", "accounting and finance",
                               "accountant and finance", "accountant and admin",
                               "accountant and office", "አካውንታንት", "አካውንቲንግ",
                               "የሂሳብ ባለሞያ", "ACCOUNTANT", "accounts"]),

    ("Cashier",              ["cashier", "ካሸር"]),

    ("Finance Officer",      ["finance officer", "finance manager", "finance and admin",
                               "finance and hr", "finance & admin", "finance & compliance",
                               "junior finance", "head of finance", "finanace manager",
                               "finance manager", "finance"]),

    ("Auditor",              ["auditor", "internal audit"]),

    # ── Software Engineering ─────────────────────────────────────────────────
    ("Software Engineer",    ["software engineer", "software developer", "programmer",
                               "backend engineer", "frontend engineer", "backend developer",
                               "frontend developer", "full stack", "fullstack",
                               "dotnet developer", "flutter", "mobile developer",
                               "web developer", "junior software", "senior software",
                               "junior backend", "senior backend", "junior full",
                               "senior full", "android developer", "ios developer",
                               "oddo programer", "odoo erp"]),

    # ── Data & AI ────────────────────────────────────────────────────────────
    ("Data Scientist",       ["data scientist", "data science"]),
    ("Data Analyst",         ["data analyst", "data entry", "data entry person"]),

    # ── DevOps ───────────────────────────────────────────────────────────────
    ("DevOps Engineer",      ["devops", "cloud engineer", "system admin",
                               "system administrator", "it administrator"]),

    # ── UI/UX ────────────────────────────────────────────────────────────────
    ("UI/UX Designer",       ["ui/ux", "ui designer", "ux designer",
                               "figma and ui", "figma designer"]),

    # ── Product Management ───────────────────────────────────────────────────
    ("Product Manager",      ["product manager", "product owner", "agile software delivery",
                               "technical pm"]),

    # ── IT Support ───────────────────────────────────────────────────────────
    ("IT Officer",           ["it officer", "it support", "it manager", "it-officer",
                               "it and program", "it teacher", "it admin",
                               "it / አይቲ", "hr/it officer", "graduate trainee - it",
                               "it administrator", "junior it operations"]),

    # ── Marketing ────────────────────────────────────────────────────────────
    ("Marketing Manager",    ["marketing manager", "digital marketing manager",
                               "marketing director", "senior marketing manager",
                               "female marketing manager", "marketing development",
                               "growth marketing manager"]),

    ("Marketing Officer",    ["marketing officer", "digital marketer", "digital marketing",
                               "marketing executive", "marketing specialist",
                               "marketing coordinator", "marketing expert",
                               "marketing research", "marketing and communication",
                               "crm & digital", "paid ads", "seo", "marketing",
                               "junior marketing", "senior digital marketer",
                               "marketing & sales support"]),

    # ── Human Resources ──────────────────────────────────────────────────────
    ("HR Manager",           ["hr manager", "human resource manager", "human resources manager",
                               "senior human resource manager", "hr and administration",
                               "head of recruitment", "people operations",
                               "people operation", "finance and hr manager"]),

    ("HR Officer",           ["hr officer", "human resource officer", "human resources officer",
                               "hr recruiter", "talent acquisition", "recruitment",
                               "personnel officer", "junior hr", "admin and hr",
                               "hr and admin", "hr / erp"]),

    # ── Administration ───────────────────────────────────────────────────────
    ("Executive Assistant",  ["executive assistant", "personal assistant",
                               "senior executive assistant"]),

    ("Secretary",            ["secretary", "executive secretary", "office secretary",
                               "apartment secretary", "head office secretary",
                               "secretary executive", "secretary/ receptionist",
                               "OFFICE SECRETARY"]),

    ("Receptionist",         ["receptionist", "reception", "front desk", "receptions",
                               "receiptionist", "hotel front desk", "call receptionist",
                               "ስፓ ሬሴፕሽኒስት", "receptionist and cashier",
                               "receptionist and secretary"]),

    ("Office Manager",       ["office manager", "admin officer", "office admin",
                               "administrative assistant", "administrative assistance",
                               "admin assistance", "admin assistant", "junior admin",
                               "office assistant", "office manager and sales",
                               "registrar / office assistant"]),

    # ── Graphic Design ───────────────────────────────────────────────────────
    ("Graphic Designer",     ["graphic design", "graphic designer", "graphics designer",
                               "graphics design", "SENIOR GRAPHICS DESIGNER",
                               "senior graphic designer", "junior graphic designer",
                               "intermediate graphic designer",
                               "graphics designer & content", "brand designer",
                               "senior brand", "presentation design specialist"]),

    # ── Video & Media Production ─────────────────────────────────────────────
    ("Video Editor",         ["video editor", "video editing", "video edittor",
                               "videographer", "video producer", "video creator",
                               "video recorder", "short form editor", "junior video editor",
                               "senior short form", "freelance video editor",
                               "full-time video editor", "video and animation",
                               "video editor trainer", "VIDEO EDITOR", "ቪዲዮ ኤዲተር",
                               "የቲክቶክ ኤዲተር", "video editor & voice over",
                               "video editor & graphic", "video editor and graphic",
                               "video editor and motion", "videographer & video editor",
                               "videographer and video editor", "VIDEOGRAPHER"]),

    ("Content Creator",      ["content creator", "content host", "ugc content",
                               "tiktok content", "tiktok live", "tiktok host",
                               "social media host", "media host", "ai content creator",
                               "arabic-speaking female content", "content lead",
                               "content creator & growth", "content creator, host",
                               "video content creator", "content creator / copywriter",
                               "content creator / storyteller", "content creator / social"]),

    ("Social Media Manager", ["social media manager", "social media managment",
                               "social media management", "social media manger",
                               "social media team leader", "social media & content",
                               "digital and social media", "marketing and social media",
                               "social media and graphic", "social media manager and graphic"]),

    # ── Writing & Content ────────────────────────────────────────────────────
    ("Script Writer",        ["script writer", "scriptwriting", "script writer and strategist",
                               "content writer", "copywriter", "content writer / script"]),

    ("Voice Over Artist",    ["voice over", "voice narrator", "english voice narrator"]),

    # ── Civil Engineering ────────────────────────────────────────────────────
    ("Civil Engineer",       ["civil engineer", "structural engineer", "site engineer",
                               "office engineer", "resident engineer", "junior civil",
                               "senior office engineer", "junior structural",
                               "structural engineers", "junior site engineer",
                               "structural darfts", "tender & quantity survey",
                               "junior sanitary", "payment follow up"]),

    ("Architect",            ["architect", "junior architect", "senior architect",
                               "sr architect", "architect /interior", "architect/ revit",
                               "technical engineer or architect", "office engineer and architect",
                               "senior arch viz"]),

    ("Quantity Surveyor",    ["quantity surveyor", "senior quantity surveyor"]),

    # ── Interior Design ──────────────────────────────────────────────────────
    ("Interior Designer",    ["interior design", "interior designer",
                               "የኢንቴሪየር ዲዛይን", "interior visualization"]),

    # ── Electrical Engineering ───────────────────────────────────────────────
    ("Electrician",          ["electrician", "building electrician", "electrical engineer",
                               "electro mechanical", "electromechanical",
                               "electrical design", "ELECTRICIAN",
                               "የቧንቧ መስመር ዝርጋታ እና የኤሌትሪክ"]),

    # ── Mechanical Engineering ───────────────────────────────────────────────
    ("Mechanical Engineer",  ["mechanical engineer", "general mechanic",
                               "hydraulic systems engineer"]),

    # ── Customer Service ─────────────────────────────────────────────────────
    ("Customer Service",     ["customer service", "customer support", "customer care",
                               "customer success", "call center", "customer handling",
                               "customer service officer", "customer service agent",
                               "customer service representative", "e-commerce assistant",
                               "customer service and admin", "customer service and reception",
                               "reception & call center"]),

    # ── Teaching & Education ─────────────────────────────────────────────────
    ("Teacher",              ["teacher", "instructor", "tutor", "online teacher",
                               "english teacher", "online english teacher",
                               "primary school", "ielts", "duolingo", "online tutor",
                               "e-tutor", "course creator", "one to one teacher",
                               "digital content teacher", "freshman course instructor",
                               "women dance teacher", "arabic language",
                               "college guidance counselor", "tutoring", "tutorial"]),

    # ── Healthcare ───────────────────────────────────────────────────────────
    ("Doctor / GP",          ["doctor", "physician", "general practitioner", "gp",
                               "medical content host"]),

    ("Nurse",                ["nurse", "home care nurse"]),

    ("Pharmacist",           ["pharmacist", "druggist", "drugist",
                               "druggist/ level iv pharmacy", "pharmacy"]),

    ("Laboratory Technician",["laboratory technician", "junior laboratory",
                               "senior laboratory", "lab technician"]),

    # ── Operations & Logistics ───────────────────────────────────────────────
    ("Driver",               ["driver", "ሹፌር", "ሹፌር isuzu", "senior sales driver",
                               "purchaser/driver", "fleet supervisor",
                               "የሞተር ሳይክል ሾፌር", "ሞተረኛ", "ጀማሪ ሞተርኛ"]),

    ("Store Keeper",         ["store keeper", "storekeeper", "store keeper",
                               "senior store keeper", "main store keeper",
                               "warehouse manager", "ስቶር ኪፐር", "furniture store keeper",
                               "workshop store keeper"]),

    ("Logistics Officer",    ["logistics", "supply chain", "deputy logistics",
                               "senior logistics", "logistics coordinator",
                               "import & export", "import/ export", "contract import"]),

    ("Procurement Officer",  ["procurement", "purchaser", "purchasing assistant",
                               "PURCHASER", "PURCHASING ASSISTANT", "የግዢ ባለሙያ",
                               "procurement officer"]),

    # ── Hospitality ──────────────────────────────────────────────────────────
    ("Waiter / Waitress",    ["waiter", "waitress", "መስተንግዶ", "አስተናጋጅ",
                               "waitress & cashier"]),

    ("Barista",              ["barista", "ባሪስታ", "restaurant barista"]),

    ("Chef",                 ["chef", "cook", "head pastry", "bakery chef",
                               "personal chef", "sandwich and breakfast chef",
                               "head pastry and backers", "የቤት ምግብ አብሳይ"]),

    ("Hotel / Restaurant Manager", ["hotel", "restaurant manager", "bar and restaurant",
                               "burger restaurant manager", "restaurant supervisor",
                               "hospitality customer care supervisor"]),

    # ── Legal ────────────────────────────────────────────────────────────────
    ("Lawyer",               ["lawyer", "legal officer", "legal counsel",
                               "compliance", "paralegal"]),

    # ── Consulting ───────────────────────────────────────────────────────────
    ("Consultant",           ["consultant", "techno-functional consultant",
                               "junior consultant"]),

    # ── Business Development ─────────────────────────────────────────────────
    ("Business Development", ["business development", "bdr", "business developer",
                               "partnership and sales", "junior business development",
                               "client growth", "account manager", "corporate account",
                               "bid expert"]),

    # ── 3D Design & Animation ────────────────────────────────────────────────
    ("3D Designer",          ["3d designer", "3d modeler", "blender 3d",
                               "blender animator", "revit model"]),

    # ── Fashion & Textile ────────────────────────────────────────────────────
    ("Fashion Designer",     ["fashion designer", "fashion tech pack",
                               "garment sample maker", "tailor", "ልብስ ሰፊ",
                               "የልብስ ስፌት", "seamstress", "የልብስ ስፌት ባለሞያ",
                               "የፋሽን ዲዛይነር"]),

    # ── Security ─────────────────────────────────────────────────────────────
    ("Security Guard",       ["security guard", "security head", "security",
                               "ጥበቃ", "event security", "Security/የጥበቃ ሠራተኛ"]),

    # ── General Engineering ──────────────────────────────────────────────────
    ("Engineering Manager",  ["engineering manager", "technical manager",
                               "plant manager", "production manager", "PRODUCTION MANAGER"]),
]

def bucket_title(raw_title: str) -> str:
    if not raw_title or pd.isna(raw_title):
        return "Other"
    t = str(raw_title).lower().strip()
    # remove parentheticals
    t_clean = re.sub(r"\(.*?\)", "", t).strip()
    for bucket_name, keywords in TITLE_BUCKETS:
        if any(kw in t_clean for kw in keywords):
            return bucket_name
    # fallback: strip seniority and title-case
    STRIP = ["senior", "junior", "mid-level", "intermediate", "lead", "head of",
        "chief", "principal", "associate", "assistant", "intern", "trainee",
        "entry level", "entry-level", "sr.", "jr.", "sr", "jr",
        "i", "ii", "iii", "iv"]
    for word in STRIP:
        t_clean = re.sub(rf"\b{word}\b", "", t_clean)
    t_clean = re.sub(r"\s+", " ", t_clean).strip()
    return t_clean.title() if t_clean else "Other"

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

    # ── normalize job title (strip seniority for grouping) ───────────────────
    df["title_normalized"] = df["title"].apply(bucket_title)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT, index=False)
    print(f"✓ Cleaned {len(df)} rows → {OUT}")
    return df

if __name__ == "__main__":
    df = pd.read_parquet(RAW)
    clean(df)
