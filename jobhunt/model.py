"""The common Job record every source is converted into, plus text helpers."""
import html
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class Job:
    source: str
    title: str
    company: str
    url: str
    location: str = ""                 # free-text location as the source gives it
    restrictions: Optional[List[str]] = None  # structured country/region list; [] = worldwide
    remote: Optional[bool] = None
    description: str = ""
    posted: Optional[datetime] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: str = ""
    salary_period: str = ""            # year / month / hour / ''
    salary_text: str = ""
    job_type: str = ""                 # full-time / contract / ...
    tags: List[str] = field(default_factory=list)

    # filled in by the pipeline
    eligibility: str = ""              # ELIGIBLE / LIKELY / CHECK / REJECT
    eligibility_reason: str = ""
    eligibility_evidence: str = ""
    salary_usd_min: Optional[float] = None
    salary_usd_max: Optional[float] = None
    salary_note: str = ""
    fit_score: int = 0
    matched_skills: List[str] = field(default_factory=list)
    gaps: List[str] = field(default_factory=list)
    region: str = ""                   # US / EMEA / MENA / JORDAN

    @property
    def key(self):
        return norm_key(self.company) + "|" + norm_key(self.title)


def norm_key(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


_TAG_RE = re.compile(r"<[^>]+>")
_BLOCK_RE = re.compile(r"</?(p|div|br|li|ul|ol|h[1-6]|tr)[^>]*>", re.I)


def html_to_text(s):
    if not s:
        return ""
    s = html.unescape(html.unescape(s)) if "&lt;" in s else html.unescape(s)
    s = _BLOCK_RE.sub("\n", s)
    s = _TAG_RE.sub(" ", s)
    s = html.unescape(s)
    s = re.sub(r"[ \t\xa0]+", " ", s)
    s = re.sub(r"\n\s*\n+", "\n\n", s)
    return s.strip()


def parse_date(v):
    """Accepts unix seconds/ms, ISO strings, or RFC-822 (RSS) dates."""
    if v is None or v == "":
        return None
    try:
        if isinstance(v, (int, float)) or (isinstance(v, str) and v.isdigit()):
            n = float(v)
            if n > 1e11:
                n /= 1000.0
            return datetime.fromtimestamp(n, tz=timezone.utc)
        s = str(v).strip()
        try:
            d = datetime.fromisoformat(s.replace("Z", "+00:00"))
        except ValueError:
            from email.utils import parsedate_to_datetime
            try:
                d = parsedate_to_datetime(s)
            except (TypeError, ValueError):
                d = None
                for fmt in ("%B %d, %Y", "%b %d, %Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                    try:
                        d = datetime.strptime(s, fmt)
                        break
                    except ValueError:
                        continue
                if d is None:
                    return None
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d
    except Exception:
        return None


def to_float(v):
    if v is None or v == "":
        return None
    try:
        f = float(str(v).replace(",", ""))
        return f if f > 0 else None
    except ValueError:
        return None
