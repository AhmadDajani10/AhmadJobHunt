"""Write the outreach email + LinkedIn note for each job, offline and free.

Drafts use the placeholder {FIRST_NAME}; the report swaps in the contact's name as you
type it. Each job also gets a ready-made prompt you can paste into Claude if you want a
more polished rewrite (uses your existing Claude plan, no extra cost).
"""
import re

PLACEHOLDER = "{FIRST_NAME}"


def pick_achievements(job, achievements, n=2):
    text = (job.title + " " + job.description).lower()
    scored = []
    for i, a in enumerate(achievements):
        hits = 0
        for k in a["keywords"]:
            k = k.strip().lower()
            pat = r"\b" + re.escape(k) + (r"\b" if len(k) <= 3 else "")  # short words must match whole
            hits += bool(re.search(pat, text))
        scored.append((hits, -i, a))
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    picked = [a for hits, _, a in scored if hits > 0][:n]
    for a in achievements:  # top up with the defaults (first in the list) if few matched
        if len(picked) >= n:
            break
        if a not in picked:
            picked.append(a)
    return picked


def _overlap_line(job):
    if job.region == "JORDAN":
        return "I'm local to Amman and available to work on-site."
    if job.region == "EMEA":
        return "Amman is only 1–2 hours ahead of most of Europe, so I'd share your full working day."
    if job.region == "MENA":
        return "I'm in the same time zone as most of the Gulf, give or take an hour."
    return ("I've worked fully remote for a US company for the past five years and can keep full overlap "
            "with US Eastern hours.")


def _skills_clause(job, max_n=3):
    prefer = ["Azure Data Factory", "Power BI", "SSIS", "Python", "SQL", "Power Platform", "Power Apps",
              "Power Automate", "Tableau", "data pipelines", "ETL/ELT", "Logic Apps", "SQL Server", "DAX"]
    s = [x for x in prefer if x in job.matched_skills][:max_n]
    if len(s) >= 2:
        return " — especially " + ", ".join(s[:-1]) + " and " + s[-1]
    return ""


def build_drafts(job, profile):
    first = profile["name"].split()[0]
    picks = pick_achievements(job, profile["achievements"])
    remote_note = ""
    if job.region != "JORDAN":
        remote_note = (" Happy to work as a contractor or through an employer-of-record, whichever is easiest "
                       "for your team.")
    title = job.title.strip()
    company = job.company.strip()
    subject = f"{title} at {company} — {profile['headline_short']}"
    sig = "\n".join(x for x in [profile["name"], profile.get("signature_line", "")] if x)
    body = (
        f"Hi {PLACEHOLDER},\n\n"
        f"I'm applying for the {title} role at {company} through your careers page and wanted to reach out "
        f"directly. I'm a {profile['current_title']} with {profile['years_experience']}+ years building "
        f"production data platforms, and the role lines up closely with my day-to-day work{_skills_clause(job)}.\n\n"
        f"A couple of relevant results:\n"
        + "".join(f"• {a['text']}\n" for a in picks)
        + f"\nOn logistics: I'm a US and Jordanian citizen based in Amman (UTC+3). {_overlap_line(job)}"
        + f"{remote_note}\n\n"
        f"Would you be open to a short call? My resume is attached.\n\n"
        f"Best,\n{sig}"
    )
    note = (f"Hi {PLACEHOLDER}, I'm applying for {title} at {company}. I'm a {profile['current_title']} "
            f"(Azure, SQL, Python; 400+ production pipelines), US/Jordanian citizen in Amman. "
            f"Would love to connect.")
    if len(note) > 290:  # LinkedIn connection notes cap at 300 chars
        note = (f"Hi {PLACEHOLDER}, I'm applying for {title[:60]} at {company[:40]}. Principal BI Data Engineer "
                f"(Azure/SQL/Python), based in Amman. Would love to connect.")
    prompt = claude_prompt(job, profile)
    return {"subject": subject, "body": body, "linkedin_note": note, "claude_prompt": prompt, "first": first}


def claude_prompt(job, profile):
    desc = job.description[:7000]
    return f"""Write a short, specific cold email from me to the recruiter or hiring manager for the job below.

Rules:
- Under 150 words in the body, plus a subject line. Plain, confident, no buzzwords or flattery.
- Open with the role and that I'm applying. Then 2 results from my resume that most directly match what this posting asks for (use the real numbers).
- State plainly that I'm a US and Jordanian citizen living in Amman, Jordan (UTC+3), and how my hours overlap with their team. Offer contractor or employer-of-record if they're outside Jordan.
- Ask for a short call. Address the person as {PLACEHOLDER}.
- Also give me a LinkedIn connection note under 280 characters.
- After the drafts, list any requirements in the posting I don't clearly meet, and one honest sentence I could use for each.

MY RESUME
{profile['resume_text']}

THE JOB
Title: {job.title}
Company: {job.company}
Location: {job.location}
Link: {job.url}

{desc}
"""
