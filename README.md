# AhmadJobHunt

Finds tech jobs Ahmad can do **from Jordan** (remote for US/EU/Gulf companies, or on-site in Jordan with big employers), filters out anything that pays under **$80K/yr** or requires living in the US, and prepares everything needed to reach out:

- **Why it's eligible:** the exact posting text that shows Jordan is OK (or why to double-check)
- **Fit score:** how well it matches the resume, plus skill gaps to prepare for
- **Contacts:** names/emails found in the posting, one-click LinkedIn/Google searches for the recruiter and hiring manager, and likely email addresses once you have a name
- **Drafts:** a tailored email and a LinkedIn connection note, an **Open in Gmail** button, and a ready-made prompt to paste into Claude for a sharper rewrite

Nothing is ever sent automatically. You review, then send.

## Run it

**One-time setup:** install Python 3.9 or newer from [python.org](https://www.python.org/downloads/). On Windows, tick **"Add python.exe to PATH"** in the installer. No other installs or accounts needed.

1. Download this repo: green **Code** button → **Download ZIP**, and unzip it. (Or `git clone` it.)
2. Start it:
   - **Windows:** double-click `run_windows.bat`
   - **Mac:** double-click `run_mac.command`. The first time, right-click it → **Open** to get past the security prompt.
   - **Any terminal:** `python hunt.py` (or `python3 hunt.py`)
3. The first run asks for your email, phone and LinkedIn URL for the email signature. They're saved only on your computer in `config/private.json`, which is never uploaded.
4. Your browser opens the report. Run it once a day; jobs you haven't seen before are marked **NEW**.

## Using the report

1. Open a posting and read it. Apply through their careers page.
2. Expand **Contact & drafts** and click a LinkedIn search to find the recruiter or hiring manager. Hiring managers often reply more than recruiters.
3. Type their name. The email greeting updates, and likely addresses appear.
   - Addresses are **unverified guesses**. Prefer an address found in the posting, or message them on LinkedIn with the connection note.
4. Edit the draft if you want, then **Open in Gmail** (or copy it) and send.
5. Mark the job **Applied / Emailed / Skip**. Your marks and edits are saved in your browser.

## Settings (`config/settings.json`)

| Setting | What it does |
|---|---|
| `min_salary_usd` | Pay floor. Jobs listing a max below this are dropped; jobs with no salary are kept. |
| `max_age_days` | Ignore postings older than this. |
| `search_terms` | Job titles/keywords to search for. |
| `sources` | Turn individual job sites on/off. |
| `watchlist` | Company career boards to check. After each run, boards that didn't load are listed so you can remove them. |
| `min_fit_score` | Hide weak matches (0–100). |

Resume facts used in the drafts live in `config/profile.json`.

## How eligibility is judged

- **Eligible:** open worldwide, Jordan named, or located in Jordan.
- **Likely:** open to EMEA / Middle East, or the posting says they hire internationally (via Deel, an employer of record, contractors, etc.).
- **Check:** remote with no region stated, Europe-only, or conflicting signals. Worth a one-line question to the recruiter.
- **Ruled out:** US/Americas-only, requires US residency or a security clearance, tied to another country, on-site outside Jordan, or pays under the floor. The report lists counts by reason.

## Sources

Free public feeds only: [Himalayas](https://himalayas.app), [Remotive](https://remotive.com), [RemoteOK](https://remoteok.com), [Jobicy](https://jobicy.com), [Working Nomads](https://www.workingnomads.com), [We Work Remotely](https://weworkremotely.com), [Amazon Jobs](https://www.amazon.jobs) (Jordan), and company boards on Greenhouse, Lever and Ashby. Every listing links back to its original posting.

LinkedIn, Indeed and Bayt don't offer public feeds, and scraping them breaks their terms. The report has a **"do these by hand"** panel with pre-filtered links for them, plus talent networks that place people abroad at US rates.

Responses are cached for 6 hours to stay polite to these sites. Use `python hunt.py --refresh` to force fresh data.

## Tests

```
python -m unittest discover tests
```
