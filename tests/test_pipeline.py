"""Offline end-to-end test: fake API responses -> full pipeline -> report.

Run:  python -m unittest discover tests
"""
import json
import sys
import tempfile
import time
import unittest
from argparse import Namespace
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import hunt  # noqa: E402
from jobhunt.http import FetchError  # noqa: E402
from jobhunt.filters import parse_salary_text  # noqa: E402

NOW = int(time.time())
ISO = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(NOW - 86400))
OLD = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(NOW - 86400 * 60))
DESC = ("<p>We need SQL, Python, Azure Data Factory and Power BI. Build data pipelines and dashboards. "
        "Snowflake and dbt a plus.</p>")

FIXTURES = {
    "himalayas.app/jobs/api/search": {"jobs": [
        {"title": "Senior Data Engineer", "companyName": "Globex", "applicationLink": "https://himalayas.app/companies/globex/jobs/sde",
         "locationRestrictions": [], "description": DESC, "pubDate": NOW - 3600, "minSalary": 100000, "maxSalary": 140000, "currency": "USD"},
        {"title": "BI Developer", "companyName": "USOnly Inc", "applicationLink": "https://himalayas.app/x/1",
         "locationRestrictions": ["United States"], "description": DESC, "pubDate": NOW - 3600},
        {"title": "Analytics Engineer", "companyName": "Mideast Co", "applicationLink": "https://himalayas.app/x/2",
         "locationRestrictions": ["Germany", "Jordan"], "description": DESC, "pubDate": NOW - 7200},
        {"title": "Power BI Developer", "companyName": "Cheap Ltd", "applicationLink": "https://himalayas.app/x/3",
         "locationRestrictions": [], "description": DESC, "pubDate": NOW - 7200, "minSalary": 30000, "maxSalary": 40000, "currency": "USD"},
        {"title": "Data Engineer", "companyName": "Stale Corp", "applicationLink": "https://himalayas.app/x/4",
         "locationRestrictions": [], "description": DESC, "pubDate": NOW - 86400 * 90},
    ]},
    "remotive.com": {"jobs": [
        {"title": "Senior Data Engineer", "company_name": "Initech", "url": "https://remotive.com/j/1",
         "candidate_required_location": "USA Only", "description": DESC, "publication_date": ISO, "salary": ""},
        {"title": "Power Platform Developer", "company_name": "EuroSoft", "url": "https://remotive.com/j/2",
         "candidate_required_location": "EMEA", "description": "<p>Power Apps, Power Automate, Dataverse. SharePoint workflows.</p>",
         "publication_date": ISO, "salary": "$85k - $110k"},
        {"title": "Senior Data Analyst", "company_name": "Hooli", "url": "https://remotive.com/j/3",
         "candidate_required_location": "Worldwide", "description": DESC + "<p>Candidates must reside in the United States.</p>",
         "publication_date": ISO},
    ]},
    "remoteok.com/api": [
        {"legal": "notice"},
        {"position": "Staff Analytics Engineer", "company": "Distributed Inc", "url": "https://remoteok.com/l/1",
         "location": "", "description": DESC + " We hire through Deel in 100+ countries.", "epoch": NOW - 5000,
         "salary_min": 120000, "salary_max": 160000, "tags": ["data"]},
        {"position": "Frontend Engineer", "company": "Webby", "url": "https://remoteok.com/l/2", "location": "Worldwide",
         "description": "React", "epoch": NOW},
    ],
    "jobicy.com": {"jobs": [
        {"jobTitle": "Senior BI Engineer", "companyName": "Berlin Data GmbH", "url": "https://jobicy.com/j/1", "jobGeo": "Europe",
         "jobDescription": DESC, "pubDate": ISO, "annualSalaryMin": 70000, "annualSalaryMax": 90000, "salaryCurrency": "EUR"},
    ]},
    "workingnomads.com": [
        {"title": "Data Engineer (Contract)", "company_name": "NomadCo", "url": "https://workingnomads.com/j/1",
         "location": "Anywhere", "description": DESC, "pub_date": ISO, "tags": "sql,python"},
    ],
    "weworkremotely.com": """<?xml version="1.0"?><rss><channel>
        <item><title>Acme: Senior Data Engineer</title><region>USA Only</region><link>https://weworkremotely.com/j/1</link>
        <description>&lt;p&gt;SQL Python&lt;/p&gt;</description><pubDate>Mon, 10 Nov 2026 10:00:00 +0000</pubDate></item>
        </channel></rss>""",
    "amazon.jobs": {"jobs": [
        {"title": "Business Intelligence Engineer, Amazon Payments", "company_name": "Amazon", "job_path": "/en/jobs/123/bie",
         "normalized_location": "Amman, JOR", "description": "SQL, Python, dashboards, data pipelines.", "posted_date": "November 10, 2026"},
        {"title": "Software Development Engineer", "company_name": "Amazon", "job_path": "/en/jobs/124/sde",
         "normalized_location": "Amman, JOR", "description": "Java", "posted_date": "November 10, 2026"},
    ]},
    "greenhouse.io/v1/boards/gitlab": {"jobs": [
        {"title": "Senior Data Engineer", "absolute_url": "https://job-boards.greenhouse.io/gitlab/jobs/1",
         "location": {"name": "Remote, EMEA"}, "updated_at": ISO,
         "content": "&lt;p&gt;Python, SQL, dbt, Snowflake pipelines. Questions? Contact Jane Smith at jane.smith@gitlab.com&lt;/p&gt;"},
        {"title": "Data Engineer", "absolute_url": "https://job-boards.greenhouse.io/gitlab/jobs/2",
         "location": {"name": "Remote, US"}, "updated_at": ISO, "content": "&lt;p&gt;Python&lt;/p&gt;"},
        {"title": "Data Engineer", "absolute_url": "https://job-boards.greenhouse.io/gitlab/jobs/3",
         "location": {"name": "Remote"}, "updated_at": ISO,
         "content": "&lt;p&gt;Python. Requires an active TS/SCI security clearance.&lt;/p&gt;"},
        {"title": "Data Engineer", "absolute_url": "https://job-boards.greenhouse.io/gitlab/jobs/4",
         "location": {"name": "Remote, EMEA"}, "updated_at": ISO, "content": "&lt;p&gt;Python, SQL&lt;/p&gt;"},
    ]},
    "api.lever.co/v0/postings/binance": [
        {"text": "Data Engineer - Data Platform", "hostedUrl": "https://jobs.lever.co/binance/1", "workplaceType": "remote",
         "categories": {"location": "Asia", "commitment": "Full-time"}, "descriptionPlain": "Spark, Kafka, Python, SQL pipelines",
         "createdAt": (NOW - 3600) * 1000},
    ],
    "posting-api/job-board/posthog": {"jobs": [
        {"title": "Data Engineer", "jobUrl": "https://jobs.ashbyhq.com/posthog/1", "isRemote": True, "location": "Remote (EMEA)",
         "descriptionPlain": "Python, SQL, data pipelines", "publishedAt": ISO, "isListed": True,
         "compensation": {"summaryComponents": [{"compensationType": "Salary", "interval": "1 YEAR", "currencyCode": "GBP",
                                                 "minValue": 90000, "maxValue": 120000}]}},
    ]},
}


class FakeFetcher:
    def _find(self, url):
        for k, v in FIXTURES.items():
            if k in url:
                return v
        raise FetchError(url, 404, "not available")

    def get_json(self, url):
        v = self._find(url)
        if isinstance(v, str):
            raise FetchError(url, None, "not JSON")
        return json.loads(json.dumps(v))

    def get_text(self, url):
        v = self._find(url)
        return v if isinstance(v, str) else json.dumps(v)


class PipelineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        hunt.OUT = Path(cls.tmp.name) / "output"
        hunt.DATA = Path(cls.tmp.name) / "data"
        hunt.log = lambda *a: None
        cls.out, cls.summary = hunt.run(Namespace(refresh=False, no_open=True, days=None), fetcher=FakeFetcher(),
                                        open_browser=False)
        cls.by = {(j["company"], j["title"]): j for j in cls.out}

    def test_eligible_and_rejected(self):
        b = self.by
        self.assertEqual(b[("Globex", "Senior Data Engineer")]["eligibility"], "ELIGIBLE")
        self.assertEqual(b[("Mideast Co", "Analytics Engineer")]["eligibility"], "ELIGIBLE")
        self.assertEqual(b[("Amazon", "Business Intelligence Engineer, Amazon Payments")]["eligibility"], "ELIGIBLE")
        self.assertEqual(b[("EuroSoft", "Power Platform Developer")]["eligibility"], "LIKELY")
        self.assertEqual(b[("Distributed Inc", "Staff Analytics Engineer")]["eligibility"], "LIKELY")
        self.assertEqual(b[("Hooli", "Senior Data Analyst")]["eligibility"], "CHECK")
        self.assertEqual(b[("Gitlab", "Senior Data Engineer")]["eligibility"], "LIKELY")
        self.assertEqual(b[("Posthog", "Data Engineer")]["eligibility"], "LIKELY")
        titles = {k[0] for k in b}
        for gone in ("USOnly Inc", "Cheap Ltd", "Stale Corp", "Initech", "Acme", "Webby"):
            self.assertNotIn(gone, titles)
        self.assertNotIn(("Amazon", "Software Development Engineer"), b)
        # GitLab posts "Data Engineer" three times (US-only, clearance, EMEA): the EMEA one must win
        self.assertEqual(b[("Gitlab", "Data Engineer")]["eligibility"], "LIKELY")
        self.assertIn("jobs/4", b[("Gitlab", "Data Engineer")]["url"])
        self.assertEqual(self.summary["rejected"], 4)

    def test_same_title_keeps_eligible_version(self):
        # Mideast Co's role is remote and names Jordan -> eligible, but no on-site line in the email
        j = self.by[("Mideast Co", "Analytics Engineer")]
        self.assertNotIn("on-site", j["drafts"]["body"])

    def test_salary_conversion(self):
        j = self.by[("Berlin Data GmbH", "Senior BI Engineer")]
        self.assertIn("converted from EUR", j["salary_note"])
        self.assertIn("$97k", j["salary_note"])  # 90k EUR -> ~97k USD

    def test_contacts_and_drafts(self):
        j = self.by[("Gitlab", "Senior Data Engineer")]
        self.assertIn("jane.smith@gitlab.com", [e["email"] for e in j["contacts"]["emails"]])
        self.assertIn("Jane Smith", j["contacts"]["people"])
        self.assertEqual(j["contacts"]["domain"], "gitlab.com")
        d = j["drafts"]
        self.assertIn("{FIRST_NAME}", d["body"])
        self.assertIn("Amman", d["body"])
        self.assertIn("Europe", d["body"])  # EMEA overlap line
        self.assertLessEqual(len(d["linkedin_note"].replace("{FIRST_NAME}", "Jonathan")), 300)
        us = self.by[("Globex", "Senior Data Engineer")]["drafts"]["body"]
        self.assertIn("US Eastern", us)
        self.assertIn("400+", us)

    def test_report_written(self):
        html = (hunt.OUT / "report.html").read_text()
        self.assertIn("Senior Data Engineer", html)
        self.assertTrue((hunt.OUT / "jobs.csv").exists())

    def test_salary_parser(self):
        self.assertEqual(parse_salary_text("$85k - $110k")[:2], (85000, 110000))
        self.assertEqual(parse_salary_text("€60,000–80,000 per year")[2], "EUR")
        self.assertEqual(parse_salary_text("$50/hr")[3], "hour")


if __name__ == "__main__":
    unittest.main()
