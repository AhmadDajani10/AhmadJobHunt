"""Free contact discovery.

1. Pull any names/emails the posting itself gives (some postings name the recruiter).
2. Build one-click LinkedIn and Google searches for the recruiter and the likely hiring
   manager. LinkedIn can't be scraped without breaking its terms, so you click and pick.
3. Guess the company's email domain so the report can suggest likely address formats
   once you have a name. These guesses are unverified and are labeled that way.
"""
import re
import urllib.parse

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
BAD_EMAIL = re.compile(r"no-?reply|donotreply|privacy|accommodat|accessib|legal|security|support@|abuse|gdpr|dataprotection|example\.com", re.I)
INBOX_EMAIL = re.compile(r"^(jobs|careers|career|recruit\w*|talent\w*|hr|hiring|people|apply)@", re.I)
NAME_RE = re.compile(
    r"(?i:recruiter|hiring manager|talent partner|talent acquisition|reach out to|contact|questions\??\s*(?:email|contact)?)"
    r"\s*(?:is|:|-|,)?\s*([A-Z][a-z]+(?:\s[A-Z][a-z'\-]+){1,2})")
NOT_NAMES = {"Talent Acquisition", "Hiring Manager", "Human Resources", "People Team", "Equal Opportunity",
             "United States", "Job Description", "Apply Now", "The Team", "Our Team"}

ATS_HOSTS = ("greenhouse.io", "lever.co", "ashbyhq.com", "workable.com", "smartrecruiters.com", "himalayas.app",
             "remotive.com", "remoteok.com", "jobicy.com", "workingnomads.com", "weworkremotely.com",
             "amazon.jobs", "bamboohr.com", "recruitee.com", "breezy.hr", "myworkdayjobs.com", "jobvite.com",
             "linkedin.com", "indeed.com", "teamtailor.com", "personio", "rippling.com", "icims.com", "wellfound.com")

COMPANY_SUFFIX = re.compile(r"\b(inc|llc|ltd|limited|gmbh|corp|corporation|co|plc|bv|sa|ag|group|technologies|labs?)\b\.?", re.I)


def _hiring_manager_titles(title):
    t = title.lower()
    if re.search(r"power (platform|apps|automate)", t):
        return ["Power Platform lead", "automation manager", "head of IT"]
    if re.search(r"\bbi\b|business intelligence|power ?bi|analyst|analytics|reporting", t):
        return ["head of analytics", "BI manager", "head of data"]
    return ["head of data", "data engineering manager", "director of data"]


def li_people(keywords):
    return "https://www.linkedin.com/search/results/people/?keywords=" + urllib.parse.quote(keywords)


def google(query):
    return "https://www.google.com/search?q=" + urllib.parse.quote(query)


def guess_domain(job, emails):
    for e in emails:
        dom = e.split("@", 1)[1].lower()
        if not any(h in dom for h in ("gmail.", "outlook.", "yahoo.", "hotmail.")):
            return dom, "from an email address in the posting"
    host = urllib.parse.urlparse(job.url).netloc.lower()
    if host and not any(h in host for h in ATS_HOSTS):
        host = re.sub(r"^(www|careers|jobs|apply)\.", "", host)
        return host, "from the job link"
    name = COMPANY_SUFFIX.sub("", job.company or "").strip().lower()
    name = re.sub(r"[^a-z0-9]", "", name)
    return (name + ".com" if name else ""), "guessed from the company name — confirm on their website"


def find_contacts(job):
    text = job.description or ""
    emails = sorted({e.rstrip(".") for e in EMAIL_RE.findall(text) if not BAD_EMAIL.search(e)})
    people = []
    for m in NAME_RE.finditer(text):
        name = m.group(1).strip()
        if name not in NOT_NAMES and name not in people:
            people.append(name)
    domain, domain_src = guess_domain(job, emails)
    company = job.company.strip()
    hm = _hiring_manager_titles(job.title)
    searches = [
        {"label": "Recruiters at " + company, "url": li_people(f"{company} recruiter")},
        {"label": "Talent acquisition at " + company, "url": li_people(f"{company} talent acquisition")},
    ] + [{"label": f"{h[0].upper() + h[1:]} at {company}", "url": li_people(f"{company} {h}")} for h in hm[:2]] + [
        {"label": "Google: LinkedIn profiles (recruiting)",
         "url": google(f'site:linkedin.com/in "{company}" (recruiter OR "talent acquisition" OR "talent partner")')},
        {"label": "Google: LinkedIn profiles (" + hm[0] + ")",
         "url": google(f'site:linkedin.com/in "{company}" ("{hm[0]}" OR "{hm[1]}")')},
        {"label": "Google: company email format", "url": google(f'"@{domain}" email format') if domain else ""},
    ]
    return {
        "emails": [{"email": e, "kind": "careers inbox" if INBOX_EMAIL.search(e) else "person"} for e in emails],
        "people": people[:3],
        "domain": domain,
        "domain_source": domain_src,
        "searches": [s for s in searches if s["url"]],
    }
