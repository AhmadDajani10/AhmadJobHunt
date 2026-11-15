"""Adapters for free, public job feeds. Each returns a list of Job records.

Only official public APIs / RSS feeds are used. No scraping of LinkedIn, Indeed or
anything behind a login.
"""
import time
import urllib.parse
import xml.etree.ElementTree as ET

from .http import FetchError
from .model import Job, html_to_text, parse_date, to_float

q = urllib.parse.quote_plus


def _list(v):
    if v is None:
        return []
    if isinstance(v, list):
        return [str(x) for x in v if x]
    return [str(v)]


# ---------------------------------------------------------------- Himalayas
def himalayas(fetcher, settings, log):
    """himalayas.app search, filtered server-side to jobs that can be done from Jordan (country=JO).
    Rate-limited, so requests are paced; results are cached for a few hours."""
    raw = []
    pages = settings.get("himalayas_pages", 2)
    terms = settings.get("himalayas_terms") or settings["search_terms"]
    failed = []
    for term in terms:
        for page in range(1, pages + 1):
            try:
                data = fetcher.get_json(
                    f"https://himalayas.app/jobs/api/search?q={urllib.parse.quote(term)}&country=JO&page={page}")
            except FetchError as e:
                failed.append(e)
                break  # move on to the next search term
            jobs = data.get("jobs") or []
            raw.extend(jobs)
            if len(jobs) < 20:
                break
    if failed and not raw:
        raise failed[0]
    if failed:
        log(f"  himalayas: {len(failed)} search(es) refused ({failed[0].status or 'error'}); kept {len(raw)} postings")
    out = []
    for j in raw:
        restr = j.get("locationRestrictions")
        if isinstance(restr, list):
            restr = [r.get("name", r) if isinstance(r, dict) else r for r in restr]
        out.append(Job(
            source="Himalayas",
            title=j.get("title", ""),
            company=j.get("companyName", ""),
            url=j.get("applicationLink") or j.get("guid") or "",
            location=", ".join(_list(restr)) or "Worldwide",
            restrictions=restr if isinstance(restr, list) else None,
            remote=True,
            description=html_to_text(j.get("description") or j.get("excerpt")),
            posted=parse_date(j.get("pubDate")),
            salary_min=to_float(j.get("minSalary")),
            salary_max=to_float(j.get("maxSalary")),
            salary_currency=j.get("currency") or "USD",
            salary_period={"hourly": "hour", "monthly": "month", "weekly": "week", "daily": "day"}.get(
                (j.get("salaryPeriod") or "").lower(), "year"),
            job_type=j.get("employmentType") or "",
            tags=_list(j.get("categories")),
        ))
    return out


# ---------------------------------------------------------------- Remotive
def remotive(fetcher, settings, log):
    """remotive.com: asks that you link back and not poll more than a few times a day."""
    urls = ["https://remotive.com/api/remote-jobs?category=data"]
    urls += [f"https://remotive.com/api/remote-jobs?search={q(t)}" for t in ("power bi", "power platform", "business intelligence")]
    out = []
    for url in urls:
        data = fetcher.get_json(url)
        for j in data.get("jobs", []):
            out.append(Job(
                source="Remotive",
                title=j.get("title", ""),
                company=j.get("company_name", ""),
                url=j.get("url", ""),
                location=j.get("candidate_required_location") or "",
                remote=True,
                description=html_to_text(j.get("description")),
                posted=parse_date(j.get("publication_date")),
                salary_text=j.get("salary") or "",
                job_type=j.get("job_type") or "",
                tags=_list(j.get("tags")),
            ))
    return out


# ---------------------------------------------------------------- RemoteOK
def remoteok(fetcher, settings, log):
    """remoteok.com: terms ask you to link back to the listing (the report does)."""
    data = fetcher.get_json("https://remoteok.com/api")
    out = []
    for j in data if isinstance(data, list) else []:
        if not isinstance(j, dict) or not j.get("position"):
            continue  # first element is a legal notice
        out.append(Job(
            source="RemoteOK",
            title=j.get("position", ""),
            company=j.get("company", ""),
            url=j.get("url") or j.get("apply_url") or "",
            location=j.get("location") or "",
            remote=True,
            description=html_to_text(j.get("description")),
            posted=parse_date(j.get("epoch") or j.get("date")),
            salary_min=to_float(j.get("salary_min")),
            salary_max=to_float(j.get("salary_max")),
            salary_currency="USD",
            salary_period="year",
            tags=_list(j.get("tags")),
        ))
    return out


# ---------------------------------------------------------------- Jobicy
def jobicy(fetcher, settings, log):
    out = []
    for tag in ("data engineer", "business intelligence", "power bi", "analytics", "data"):
        data = fetcher.get_json(f"https://jobicy.com/api/v2/remote-jobs?count=50&tag={q(tag)}")
        for j in data.get("jobs", []):
            out.append(Job(
                source="Jobicy",
                title=html_to_text(j.get("jobTitle", "")),
                company=j.get("companyName", ""),
                url=j.get("url", ""),
                location=j.get("jobGeo") or "",
                remote=True,
                description=html_to_text(j.get("jobDescription") or j.get("jobExcerpt")),
                posted=parse_date(j.get("pubDate")),
                salary_min=to_float(j.get("annualSalaryMin")),
                salary_max=to_float(j.get("annualSalaryMax")),
                salary_currency=j.get("salaryCurrency") or "USD",
                salary_period="year",
                job_type=", ".join(_list(j.get("jobType"))),
            ))
    return out


# ---------------------------------------------------------------- Working Nomads
def workingnomads(fetcher, settings, log):
    data = fetcher.get_json("https://www.workingnomads.com/api/exposed_jobs/")
    out = []
    for j in data if isinstance(data, list) else []:
        out.append(Job(
            source="Working Nomads",
            title=j.get("title", ""),
            company=j.get("company_name", ""),
            url=j.get("url", ""),
            location=j.get("location") or "",
            remote=True,
            description=html_to_text(j.get("description")),
            posted=parse_date(j.get("pub_date")),
            tags=_list(j.get("tags")) if not isinstance(j.get("tags"), str) else j["tags"].split(","),
        ))
    return out


# ---------------------------------------------------------------- We Work Remotely (RSS)
def weworkremotely(fetcher, settings, log):
    out = []
    for feed in ("remote-jobs.rss",):
        text = fetcher.get_text(f"https://weworkremotely.com/{feed}")
        root = ET.fromstring(text.encode("utf-8"))
        for item in root.iter("item"):
            def t(tag):
                el = item.find(tag)
                return (el.text or "").strip() if el is not None else ""
            title = t("title")
            company, _, role = title.partition(":")
            if not role:
                company, role = "", title
            out.append(Job(
                source="We Work Remotely",
                title=role.strip(),
                company=company.strip(),
                url=t("link"),
                location=t("region"),
                remote=True,
                description=html_to_text(t("description")),
                posted=parse_date(t("pubDate")),
                job_type=t("type"),
            ))
    return out


# ---------------------------------------------------------------- Amazon (on-site Jordan)
def amazon_jordan(fetcher, settings, log):
    """Amazon has a large engineering office in Amman. On-site roles in Jordan."""
    out = []
    for offset in (0, 100, 200):
        data = fetcher.get_json(
            f"https://www.amazon.jobs/en/search.json?country=JOR&result_limit=100&offset={offset}&sort=recent")
        jobs = data.get("jobs") or []
        for j in jobs:
            path = j.get("job_path") or ""
            desc = "\n\n".join(filter(None, [
                html_to_text(j.get("description")),
                "Basic qualifications:\n" + html_to_text(j.get("basic_qualifications")) if j.get("basic_qualifications") else "",
                "Preferred qualifications:\n" + html_to_text(j.get("preferred_qualifications")) if j.get("preferred_qualifications") else "",
            ]))
            out.append(Job(
                source="Amazon Jobs",
                title=j.get("title", ""),
                company=j.get("company_name") or "Amazon",
                url=("https://www.amazon.jobs" + path) if path.startswith("/") else (j.get("url_next_step") or path),
                location=j.get("normalized_location") or j.get("location") or "Amman, Jordan",
                remote=False,
                description=desc,
                posted=parse_date(j.get("posted_date")),
                job_type=j.get("job_schedule_type") or "",
            ))
        if len(jobs) < 100:
            break
    return out


# ---------------------------------------------------------------- Company career boards
def _greenhouse(fetcher, token):
    data = fetcher.get_json(f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true")
    out = []
    for j in data.get("jobs", []):
        offices = ", ".join(o.get("name", "") for o in j.get("offices") or [] if o.get("name"))
        loc = (j.get("location") or {}).get("name", "")
        out.append(Job(
            source="Greenhouse",
            title=j.get("title", ""),
            company=j.get("company_name") or token,
            url=j.get("absolute_url", ""),
            location="; ".join(x for x in (loc, offices) if x),
            description=html_to_text(j.get("content")),
            posted=parse_date(j.get("first_published") or j.get("updated_at")),
        ))
    return out


def _lever(fetcher, token):
    data = fetcher.get_json(f"https://api.lever.co/v0/postings/{token}?mode=json")
    out = []
    for j in data if isinstance(data, list) else []:
        cats = j.get("categories") or {}
        locs = cats.get("allLocations") or [cats.get("location")]
        sal = j.get("salaryRange") or {}
        desc = "\n\n".join(filter(None, [j.get("descriptionPlain")] + [
            (l.get("text", "") + "\n" + html_to_text(l.get("content"))) for l in j.get("lists") or []
        ] + [j.get("additionalPlain")]))
        interval = (sal.get("interval") or "").lower()
        out.append(Job(
            source="Lever",
            title=j.get("text", ""),
            company=token,
            url=j.get("hostedUrl") or j.get("applyUrl") or "",
            location="; ".join(x for x in locs if x) + (f" ({j['workplaceType']})" if j.get("workplaceType") else ""),
            remote=(j.get("workplaceType") == "remote") if j.get("workplaceType") else None,
            description=desc,
            posted=parse_date(j.get("createdAt")),
            salary_min=to_float(sal.get("min")),
            salary_max=to_float(sal.get("max")),
            salary_currency=sal.get("currency") or "",
            salary_period="hour" if "hour" in interval else "month" if "month" in interval else "year",
            job_type=cats.get("commitment") or "",
        ))
    return out


def _ashby(fetcher, token):
    data = fetcher.get_json(f"https://api.ashbyhq.com/posting-api/job-board/{token}?includeCompensation=true")
    out = []
    for j in data.get("jobs", []):
        if j.get("isListed") is False:
            continue
        locs = [j.get("location") or ""] + [s.get("location", "") for s in j.get("secondaryLocations") or []]
        smin = smax = None
        cur = period = ""
        for c in ((j.get("compensation") or {}).get("summaryComponents") or []):
            if (c.get("compensationType") or "").lower() == "salary":
                smin, smax = to_float(c.get("minValue")), to_float(c.get("maxValue"))
                cur = c.get("currencyCode") or ""
                iv = (c.get("interval") or "").lower()
                period = "hour" if "hour" in iv else "month" if "month" in iv else "year"
                break
        out.append(Job(
            source="Ashby",
            title=j.get("title", ""),
            company=token,
            url=j.get("jobUrl") or j.get("applyUrl") or "",
            location="; ".join(x for x in locs if x) + (" (Remote)" if j.get("isRemote") else ""),
            remote=j.get("isRemote"),
            description=j.get("descriptionPlain") or html_to_text(j.get("descriptionHtml")),
            posted=parse_date(j.get("publishedAt")),
            salary_min=smin, salary_max=smax, salary_currency=cur, salary_period=period,
            salary_text=(j.get("compensation") or {}).get("compensationTierSummary") or "",
            job_type=j.get("employmentType") or "",
        ))
    return out


ATS = {"greenhouse": _greenhouse, "lever": _lever, "ashby": _ashby}


def watchlist(fetcher, settings, log):
    """Career boards of companies known for hiring remotely across many countries."""
    from concurrent.futures import ThreadPoolExecutor
    tasks = [(kind, tok) for kind, toks in settings.get("watchlist", {}).items() if kind in ATS for tok in toks]
    out, missing = [], []

    def run(task):
        kind, tok = task
        try:
            return task, ATS[kind](fetcher, tok), None
        except FetchError as e:
            return task, [], e

    with ThreadPoolExecutor(max_workers=8) as ex:
        for (kind, tok), jobs, err in ex.map(run, tasks):
            if err is not None:
                missing.append(f"{kind}:{tok}" + (f" ({err.status})" if err.status else ""))
            out.extend(jobs)
    if missing:
        log(f"  watchlist boards that didn't load (safe to remove from config/settings.json): {', '.join(missing)}")
    return out


def alert_emails(fetcher, settings, log):
    """Jobs pulled from LinkedIn / Indeed / Bayt job-alert emails. The daily cloud run reads your
    Gmail (with your permission) and writes them to data/alert_jobs.json; this just loads that file."""
    import json
    from pathlib import Path
    path = Path(settings.get("alert_jobs_file") or "data/alert_jobs.json")
    if not path.exists():
        return []
    out = []
    for j in json.loads(path.read_text(encoding="utf-8")):
        if not j.get("title") or not j.get("url"):
            continue
        out.append(Job(
            source=j.get("source") or "Job alert email",
            title=j["title"], company=j.get("company", ""), url=j["url"],
            location=j.get("location", ""),
            remote=True if "remote" in (j.get("location", "") + j.get("workplace", "")).lower() else None,
            description=j.get("description", ""),
            posted=parse_date(j.get("posted")),
            salary_text=j.get("salary", ""),
        ))
    return out


SOURCES = {
    "himalayas": himalayas,
    "remotive": remotive,
    "remoteok": remoteok,
    "jobicy": jobicy,
    "workingnomads": workingnomads,
    "weworkremotely": weworkremotely,
    "amazon_jordan": amazon_jordan,
    "watchlist": watchlist,
    "alert_emails": alert_emails,
}
