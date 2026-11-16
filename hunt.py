#!/usr/bin/env python3
"""Job hunt: run `python hunt.py` and a review page opens in your browser.

Options:
  --refresh     ignore the 6-hour cache and re-download everything
  --no-open     don't open the browser at the end
  --days N      only keep postings from the last N days (default from config/settings.json)
  --overrides F JSON file whose keys override config/settings.json (the web page's saved settings)
  --summaries F JSON of short job summaries written by Claude (default data/summaries.json)
"""
import argparse
import csv
import hashlib
import json
import sys
import time
import webbrowser
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from jobhunt.contacts import find_contacts  # noqa: E402
from jobhunt.drafts import build_drafts  # noqa: E402
from jobhunt.filters import (category, classify_location, level, meets_floor, normalize_salary,  # noqa: E402
                             score_fit, short_location)
from jobhunt.http import Fetcher  # noqa: E402
from jobhunt.summarize import summarize  # noqa: E402
from jobhunt.report import render_report  # noqa: E402
from jobhunt.sources import SOURCES  # noqa: E402

CONFIG = ROOT / "config"
OUT = ROOT / "output"
DATA = ROOT / "data"


def log(msg):
    print(msg, flush=True)


def load_private():
    """Email/phone/LinkedIn for your signature. Stored only on your computer (git-ignored)."""
    path = CONFIG / "private.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    info = {"email": "", "phone": "", "linkedin": "", "trigger_id": "", "lookup_trigger_id": ""}
    if sys.stdin.isatty():
        log("\nFirst run: a few details for your email signature (saved only on this computer, never uploaded).")
        info["email"] = input("  Your email: ").strip()
        info["phone"] = input("  Your phone (optional, e.g. +962 7X XXX XXXX): ").strip()
        info["linkedin"] = input("  Your LinkedIn URL (optional): ").strip()
        path.write_text(json.dumps(info, indent=2), encoding="utf-8")
        log(f"  Saved to {path}. Edit that file any time.\n")
    return info


def pretty_company(job):
    if job.source in ("Greenhouse", "Lever", "Ashby") and job.company == job.company.lower():
        job.company = job.company.replace("-", " ").replace("_", " ").title()


def run(args, fetcher=None, open_browser=True):
    settings = json.loads((CONFIG / "settings.json").read_text(encoding="utf-8"))
    profile = json.loads((CONFIG / "profile.json").read_text(encoding="utf-8"))
    private = load_private()
    profile["signature_line"] = " · ".join(x for x in (private.get("email"), private.get("phone"), private.get("linkedin")) if x)
    if getattr(args, "overrides", None) and Path(args.overrides).exists():
        over = json.loads(Path(args.overrides).read_text(encoding="utf-8"))
        for k in ("min_salary_usd", "max_age_days", "search_terms"):
            if over.get(k):
                settings[k] = over[k]
        log(f"  using settings saved on the web page: {', '.join(k for k in over if over.get(k))}")
    if args.days:
        settings["max_age_days"] = args.days
    summaries_path = Path(getattr(args, "summaries", None) or DATA / "summaries.json")
    claude_summaries = json.loads(summaries_path.read_text(encoding="utf-8")) if summaries_path.exists() else {}
    fetcher = fetcher or Fetcher(ROOT / ".cache", settings.get("cache_hours", 6), refresh=args.refresh)

    # 1. collect
    raw, errors = [], []
    for name, fn in SOURCES.items():
        if not settings["sources"].get(name):
            continue
        t0 = time.time()
        try:
            jobs = fn(fetcher, settings, log)
            log(f"  {name:<15} {len(jobs):>5} postings  ({time.time() - t0:.1f}s)")
            raw.extend(jobs)
        except Exception as e:  # one broken source shouldn't stop the run
            log(f"  {name:<15} FAILED: {e}")
            errors.append(f"{name}: {e}")

    if getattr(fetcher, "stale", None):
        log(f"  ({len(fetcher.stale)} request(s) were refused, so older saved results were used for them)")

    # 2. recency + role fit + eligibility, then merge duplicates (the same job is often on
    #    several boards, and one company may post the same title for US and for EMEA).
    cutoff = datetime.now(timezone.utc) - timedelta(days=settings["max_age_days"])
    floor = settings["min_salary_usd"]
    rank = {"ELIGIBLE": 0, "LIKELY": 1, "CHECK": 2, "REJECT": 3}
    best = {}
    for j in raw:
        pretty_company(j)
        if not j.title or not j.url or (j.posted and j.posted < cutoff) or score_fit(j) == 0:
            continue
        classify_location(j)
        normalize_salary(j, floor)
        cur = best.get(j.key)
        better = cur is None or (rank[j.eligibility], j.salary_usd_max is None) < (rank[cur.eligibility], cur.salary_usd_max is None)
        if better:
            best[j.key] = j
    jobs = list(best.values())
    log(f"\n{len(raw)} postings scanned → {len(jobs)} recent and relevant to your background")

    # 3. drop what can't be done from Jordan or pays under the floor
    kept, reject_reasons = [], {}
    for j in jobs:
        reason = None
        if j.eligibility == "REJECT":
            reason = j.eligibility_reason.split(":")[0]
        elif not meets_floor(j, floor):
            reason = f"Pays under ${floor:,}"
        elif j.fit_score < settings.get("min_fit_score", 0):
            reason = "Weak match to your skills"
        elif j.eligibility not in settings["show_statuses"]:
            reason = "Status hidden in settings"
        if reason:
            reject_reasons[reason] = reject_reasons.get(reason, 0) + 1
        else:
            kept.append(j)

    # 4. new-vs-seen tracking
    DATA.mkdir(exist_ok=True)
    seen_path = DATA / "seen.json"
    has_memory = seen_path.exists()
    seen = json.loads(seen_path.read_text()) if has_memory else {}
    today = datetime.now().strftime("%Y-%m-%d")
    recent = datetime.now(timezone.utc) - timedelta(hours=48)
    out = []
    to_summarize = []
    for j in kept:
        jid = hashlib.sha1(j.key.encode()).hexdigest()[:16]
        summary = claude_summaries.get(jid)
        if summary:
            summary = dict(summary, by="claude")
        else:
            summary = summarize(j)
            to_summarize.append({"id": jid, "title": j.title, "company": j.company, "location": j.location,
                                 "description": j.description[:5000]})
        # with run-to-run memory: never seen before. Without it (fresh cloud run): posted in the last 2 days.
        is_new = (j.key not in seen) if has_memory else bool(j.posted and j.posted >= recent)
        seen.setdefault(j.key, today)
        out.append({
            "id": jid, "key": j.key, "title": j.title, "summary": summary, "company": j.company, "url": j.url, "source": j.source,
            "location": short_location(j), "category": category(j.title), "level": level(j.title),
            "posted": j.posted.isoformat() if j.posted else None,
            "eligibility": j.eligibility, "eligibility_reason": j.eligibility_reason,
            "eligibility_evidence": "" if (j.eligibility_evidence == j.location and len(j.location) > 70)
            else j.eligibility_evidence[:240], "salary_note": j.salary_note,
            "job_type": j.job_type, "fit_score": j.fit_score, "matched_skills": j.matched_skills,
            "gaps": j.gaps, "is_new": is_new, "first_seen": seen[j.key],
            "contacts": find_contacts(j), "drafts": build_drafts(j, profile),
        })
    seen_path.write_text(json.dumps(seen, indent=0))

    # 5. outputs
    counts = {}
    for j in out:
        counts[j["eligibility"]] = counts.get(j["eligibility"], 0) + 1
    summary = {
        "counts": counts, "new": sum(j["is_new"] for j in out), "scanned": len(raw),
        "rejected": sum(reject_reasons.values()),
        "reject_reasons": sorted(reject_reasons.items(), key=lambda x: -x[1]), "errors": errors,
    }
    OUT.mkdir(exist_ok=True)
    (OUT / "to_summarize.json").write_text(json.dumps(to_summarize, ensure_ascii=False, indent=1), encoding="utf-8")
    report = OUT / "report.html"
    render_report(report, out, summary, settings, trigger_id=private.get("trigger_id", ""),
                  lookup_trigger_id=private.get("lookup_trigger_id", ""))
    with open(OUT / "jobs.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["eligibility", "fit", "title", "company", "location", "salary", "posted", "first_seen", "url", "why"])
        for j in sorted(out, key=lambda x: -x["fit_score"]):
            w.writerow([j["eligibility"], j["fit_score"], j["title"], j["company"], j["location"], j["salary_note"],
                        (j["posted"] or "")[:10], j["first_seen"], j["url"], j["eligibility_reason"]])

    log(f"Showing {len(out)} jobs: {counts.get('ELIGIBLE', 0)} eligible, {counts.get('LIKELY', 0)} likely, "
        f"{counts.get('CHECK', 0)} to check ({summary['new']} new). Ruled out {summary['rejected']}.")
    if errors:
        log(f"{len(errors)} source(s) failed — see the top of the report.")
    if any("CERTIFICATE_VERIFY_FAILED" in e for e in errors):
        log("\n*** Mac fix: open Finder → Applications → your Python folder → double-click "
            "'Install Certificates.command', then run this again. ***")
    log(f"\nReport: {report}")
    if open_browser and not args.no_open:
        webbrowser.open(report.as_uri())
    return out, summary


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--refresh", action="store_true")
    p.add_argument("--no-open", action="store_true")
    p.add_argument("--days", type=int)
    p.add_argument("--overrides")
    p.add_argument("--summaries", help="JSON {job_id: {overview, do, need}} written by Claude; default data/summaries.json")
    args = p.parse_args()
    log("Searching job sources…")
    run(args)


if __name__ == "__main__":
    main()
