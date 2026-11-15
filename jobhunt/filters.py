"""Decide (1) is this a role Ahmad fits, (2) can he legally/practically do it from Jordan,
(3) does it pay at least the floor. Rules are deliberately transparent: every verdict
carries the text that caused it, so you can sanity-check it in the report."""
import re

# ------------------------------------------------------------------ role fit
STRONG_TITLES = [
    r"data engineer", r"analytics engineer", r"\bbi\b.*(engineer|developer|architect)",
    r"business intelligence.*(engineer|developer|architect|lead|manager)", r"power ?bi",
    r"power platform", r"power apps", r"power automate", r"etl", r"\belt\b", r"data integration",
    r"azure data", r"data platform", r"data pipeline", r"fabric",
]
MEDIUM_TITLES = [
    r"data analyst", r"analytics", r"business intelligence", r"\bbi\b", r"reporting",
    r"sql (developer|engineer)", r"database (developer|engineer)", r"data architect",
    r"data (operations|ops)", r"data consultant", r"data specialist", r"automation (engineer|developer)",
    r"insights", r"data developer", r"data warehouse", r"\bdwh?\b",
]
EXCLUDE_TITLES = [
    r"\bintern(ship)?\b", r"\bstudent\b", r"recruit", r"account executive", r"\bsales\b(?!force)",
    r"marketing manager", r"customer success", r"\bnurse\b", r"teacher", r"tutor", r"\bphd\b",
    r"\bfrench\b|\bgerman\b|\bjapanese\b|\bkorean\b|\bmandarin\b|\bdutch\b|\bitalian\b|\bspanish speaking\b",
]

# skills on the resume -> display name
HAVE_SKILLS = {
    r"\bsql\b": "SQL", r"t-?sql": "T-SQL", r"python": "Python", r"\bazure\b": "Azure",
    r"data factory|\badf\b": "Azure Data Factory", r"logic apps?": "Logic Apps",
    r"power ?bi": "Power BI", r"power apps?": "Power Apps", r"power automate": "Power Automate",
    r"power platform": "Power Platform", r"\bssis\b": "SSIS", r"\bssrs\b": "SSRS",
    r"tableau": "Tableau", r"\bsas\b": "SAS", r"oracle": "Oracle", r"\bvba\b": "VBA", r"\bdax\b": "DAX",
    r"\betl\b|\belt\b": "ETL/ELT", r"pipelines?": "data pipelines", r"sql server|mssql": "SQL Server",
    r"\bexcel\b": "Excel", r"\baws\b": "AWS", r"agile|scrum": "Agile", r"data model": "data modeling",
    r"dashboards?": "dashboards", r"machine learning|\bml\b": "ML", r"computer vision": "computer vision",
    r"automation|automate": "automation", r"data quality": "data quality", r"monitoring": "monitoring",
    r"logistics|supply chain|manufacturing|warehouse operations": "logistics/manufacturing",
    r"healthcare|clinical|\blab\b|laboratory": "healthcare/lab data", r"sftp": "SFTP",
    r"microsoft fabric|\bfabric\b": "Microsoft Fabric",
}
# common asks he doesn't list yet -> shown as gaps so he can prep talking points
GAP_SKILLS = {
    r"databricks": "Databricks", r"snowflake": "Snowflake", r"\bdbt\b": "dbt", r"airflow": "Airflow",
    r"\bspark\b|pyspark": "Spark", r"kafka": "Kafka", r"scala": "Scala", r"\bjava\b": "Java",
    r"kubernetes|\bk8s\b": "Kubernetes", r"terraform": "Terraform", r"bigquery": "BigQuery",
    r"\bgcp\b|google cloud": "GCP", r"redshift": "Redshift", r"looker": "Looker",
    r"\bgo\b|golang": "Go", r"typescript": "TypeScript",
}


def title_fit(title):
    t = title.lower()
    if any(re.search(p, t) for p in EXCLUDE_TITLES):
        return 0
    if any(re.search(p, t) for p in STRONG_TITLES):
        return 2
    if any(re.search(p, t) for p in MEDIUM_TITLES):
        return 1
    return 0


def score_fit(job):
    level = title_fit(job.title)
    text = (job.title + " " + job.description + " " + " ".join(job.tags)).lower()
    have = sorted({name for pat, name in HAVE_SKILLS.items() if re.search(pat, text)})
    gaps = sorted({name for pat, name in GAP_SKILLS.items() if re.search(pat, text)})
    score = 45 if level == 2 else 25 if level == 1 else 0
    score += min(len(have) * 4, 40)
    t = job.title.lower()
    if re.search(r"senior|\bsr\b|staff|principal|lead|architect|manager|head of", t):
        score += 10
    if re.search(r"junior|\bjr\b|entry|graduate|associate", t):
        score -= 15
    score -= min(len(gaps) * 3, 15)
    job.fit_score = max(0, min(100, score))
    job.matched_skills = have
    job.gaps = gaps
    return level


# ------------------------------------------------------------------ location eligibility
JORDAN = r"\bjordan\b|\bamman\b|\birbid\b|\baqaba\b|\bzarqa\b"
WORLDWIDE = r"worldwide|anywhere|\bglobal(ly)?\b|all countries|work from anywhere|any location|fully distributed|\bremote\s*\(?\s*global"
REGION_OK = r"\bemea\b|\bmena\b|middle east|\bgcc\b|\barab\b|levant|europe,? middle east"
REGION_MAYBE = r"\beurope\b|\beu\b|\bcet\b|\beet\b|\buk\b|\basia\b|\bapac\b|africa|\bgmt\b|\butc\s*[+-]"
HIRE_ANYWHERE_HINTS = (
    r"(via|through|using) (deel|remote\.com|oyster|rippling|papaya|velocity global|an? employer of record|an? eor)",
    r"employer of record", r"we hire (in|across) (over |more than )?\d+ countries", r"hire (talent )?globally",
    r"open to candidates (from|in) (any|all) (country|countries|location)", r"independent contractor",
    r"location[- ]independent", r"no matter where you live", r"regardless of (your )?location",
)
US_RESIDENCY = (
    r"must (reside|live|be located|be based) (in|within) the (u\.?s\.?a?|united states|continental)",
    r"(reside|located|based|living) in the (u\.?s\.?|united states) (is|are) required",
    r"only (open|available) to (candidates|applicants|residents) (located |based |residing )?in the (u\.?s|united states|us)",
    r"remote within the (u\.?s|united states)", r"(us|u\.s\.)[- ]based (candidates|applicants|remote)",
    r"must be (located|based) in (one of the following|the following) states",
    r"\bremote\s*[-–(,]\s*(us|usa|u\.s\.|united states)\b",
)
CLEARANCE = r"security clearance|clearance (is )?required|ts/sci|top secret|public trust|\bitar\b|us persons? only"
US_LOC = (r"\bus\b|\busa\b|u\.s\.|united states|america|\bcanada\b|\blatam\b|latin america|"
          r"new york|san francisco|seattle|austin|boston|chicago|los angeles|denver|atlanta|"
          r"\b(ak|az|ca|ct|dc|fl|ga|il|ky|md|mn|nc|nj|ny|oh|pa|tn|tx|ut|va|wa|wi)\b")
OTHER_COUNTRIES = (
    r"germany|france|spain|portugal|italy|netherlands|poland|romania|ukraine|ireland|united kingdom|"
    r"england|london|berlin|sweden|norway|denmark|finland|switzerland|austria|belgium|czech|hungary|"
    r"greece|turkey|israel|india|pakistan|bangladesh|philippines|indonesia|vietnam|thailand|malaysia|"
    r"singapore|japan|korea|china|taiwan|hong kong|australia|new zealand|brazil|mexico|argentina|"
    r"colombia|chile|peru|south africa|nigeria|kenya|egypt|morocco|tunisia|uae|dubai|abu dhabi|"
    r"saudi|riyadh|qatar|doha|kuwait|bahrain|oman|lebanon|serbia|bulgaria|croatia|estonia|latvia|lithuania"
)
REGION_WORDS = {
    "MENA": r"middle east|\bmena\b|\bgcc\b|\buae\b|dubai|saudi|qatar|\barab\b",
    "EMEA": r"\bemea\b|europe|\beu\b|\buk\b|united kingdom|london|berlin|germany|france|spain|netherlands|"
            r"poland|ireland|portugal|\bcet\b|\beet\b",
}


def _find(pattern, text):
    m = re.search(pattern, text, re.I)
    if not m:
        return ""
    a, b = max(0, m.start() - 60), min(len(text), m.end() + 60)
    return "…" + text[a:b].replace("\n", " ").strip() + "…"


def classify_location(job):
    loc = (job.location or "").lower()
    desc = job.description or ""
    restr = job.restrictions
    hint = next((p for p in HIRE_ANYWHERE_HINTS if re.search(p, desc, re.I)), None)

    def set_(status, reason, evidence=""):
        job.eligibility, job.eligibility_reason, job.eligibility_evidence = status, reason, evidence

    region = "US"
    for name, pat in REGION_WORDS.items():
        if re.search(pat, loc):
            region = name
            break
    if re.search(JORDAN, loc) and job.remote is not True:
        region = "JORDAN"
    elif re.search(JORDAN, loc):
        region = "MENA"
    job.region = region

    if re.search(CLEARANCE, desc, re.I) or re.search(CLEARANCE, loc):
        return set_("REJECT", "Needs US security clearance / US-person status", _find(CLEARANCE, desc))

    # Structured restrictions (Himalayas): [] means worldwide
    if restr is not None:
        joined = ", ".join(restr)
        if not restr:
            status, reason = "ELIGIBLE", "Listed as open worldwide"
        elif re.search(JORDAN, joined, re.I):
            return set_("ELIGIBLE", "Jordan is explicitly allowed", joined)
        elif re.search(REGION_OK, joined, re.I):
            status, reason = "LIKELY", f"Open to a region that includes Jordan: {joined}"
        else:
            return set_("REJECT", f"Restricted to: {joined}", joined)
        res = next((p for p in US_RESIDENCY if re.search(p, desc, re.I)), None)
        if res:
            return set_("CHECK", reason + " — but the description mentions US residency", _find(res, desc))
        return set_(status, reason, joined or "No country restrictions")

    # On-site/hybrid in Jordan, or remote with Jordan named
    if re.search(JORDAN, loc):
        return set_("ELIGIBLE", "Jordan is named in the location" if job.remote else "Located in Jordan (on-site/hybrid)",
                    job.location)

    res = next((p for p in US_RESIDENCY if re.search(p, desc + " " + loc, re.I)), None)

    if re.search(WORLDWIDE, loc):
        if res:
            return set_("CHECK", "Says worldwide, but description mentions US residency", _find(res, desc))
        return set_("ELIGIBLE", "Open worldwide", job.location)
    if re.search(REGION_OK, loc):
        return set_("LIKELY", "Open to a region that includes Jordan", job.location)
    if res:
        return set_("REJECT", "Requires living in the US", _find(res, desc + " " + loc))
    if re.search(US_LOC, loc) and not re.search(REGION_MAYBE, loc):
        return set_("REJECT", f"US/Americas location: {job.location}", job.location)
    if re.search(OTHER_COUNTRIES, loc) and not re.search(REGION_MAYBE, loc):
        if hint:
            return set_("CHECK", f"Listed for {job.location}, but they mention hiring internationally", _find(hint, desc))
        return set_("REJECT", f"Tied to another country: {job.location}", job.location)
    if re.search(REGION_MAYBE, loc):
        return set_("CHECK", f"Region '{job.location}' — ask whether Jordan works", job.location)
    if hint:
        return set_("LIKELY", "Description says they hire internationally", _find(hint, desc))
    if job.remote is False or (loc and "remote" not in loc and job.source in ("Greenhouse", "Lever", "Ashby")):
        return set_("REJECT", f"On-site/hybrid outside Jordan: {job.location}", job.location)
    return set_("CHECK", "Remote, but the allowed countries aren't stated", job.location or "(no location given)")


# ------------------------------------------------------------------ salary
FX_TO_USD = {"USD": 1, "EUR": 1.08, "GBP": 1.27, "CAD": 0.72, "AUD": 0.65, "CHF": 1.13, "NZD": 0.6,
             "AED": 0.272, "SAR": 0.267, "QAR": 0.275, "JOD": 1.41, "SEK": 0.095, "NOK": 0.093,
             "DKK": 0.145, "PLN": 0.25, "INR": 0.012, "SGD": 0.74, "ILS": 0.27, "TRY": 0.03, "BRL": 0.18}
PERIOD_MULT = {"hour": 2080, "day": 260, "week": 52, "month": 12, "year": 1}
CUR_SYMBOL = {"$": "USD", "€": "EUR", "£": "GBP"}


def parse_salary_text(text):
    """'$90k - $120k', '€60,000–80,000 per year', '$50/hr' -> (min, max, currency, period)."""
    if not text:
        return None, None, "", ""
    t = text.lower().replace(",", "")
    cur = next((c for s, c in CUR_SYMBOL.items() if s in text), "")
    cur = cur or next((c for c in FX_TO_USD if c.lower() in t), "USD")
    nums = []
    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*(k\b)?", t):
        n = float(m.group(1))
        if m.group(2):
            n *= 1000
        if n >= 5:
            nums.append(n)
    if not nums:
        return None, None, cur, ""
    period = ("hour" if re.search(r"/\s*h(ou)?r|per hour|hourly", t) else
              "month" if re.search(r"/\s*mo|per month|monthly", t) else
              "day" if re.search(r"/\s*day|per day|daily", t) else "year")
    return min(nums), max(nums), cur, period


def normalize_salary(job, floor):
    smin, smax, cur, period = job.salary_min, job.salary_max, job.salary_currency, job.salary_period
    if smin is None and smax is None and job.salary_text:
        smin, smax, cur, period = parse_salary_text(job.salary_text)
    if smin is None and smax is None:
        job.salary_note = "Not listed"
        return
    cur = (cur or "USD").upper()
    rate = FX_TO_USD.get(cur)
    if rate is None:
        job.salary_note = f"{job.salary_text or ''} {cur} (unknown currency)".strip()
        return
    ref = smax or smin
    if not period or period == "year":
        # guess period from magnitude when the source didn't say
        period = "hour" if ref < 500 else "month" if ref < 20000 else "year"
    mult = PERIOD_MULT.get(period, 1)
    job.salary_usd_min = smin * mult * rate if smin else None
    job.salary_usd_max = smax * mult * rate if smax else None
    lo = f"${job.salary_usd_min/1000:,.0f}k" if job.salary_usd_min else "?"
    hi = f"${job.salary_usd_max/1000:,.0f}k" if job.salary_usd_max else "?"
    conv = "" if cur == "USD" and period == "year" else f" (converted from {cur}/{period})"
    job.salary_note = f"{lo}–{hi} per year{conv}"


def meets_floor(job, floor):
    top = job.salary_usd_max or job.salary_usd_min
    return top is None or top >= floor
