"""Turn a long job description into a short 'at a glance' summary.

Works offline with simple rules (find the role overview, the responsibilities and the
requirements sections, keep the first few lines of each). When the daily cloud run is
used, Claude writes better summaries to data/summaries.json and those take priority.
"""
import re

ROLE_HDR = re.compile(r"^(the role|about the role|role overview|the position|about the position|the opportunity|"
                      r"position overview|job summary|summary|overview|your mission|the job)\b", re.I)
DO_HDR = re.compile(r"(responsibilit|what you('| wi)ll (do|build|own|work on)|what you will (do|build)|your role|in this role|"
                    r"day[- ]to[- ]day|your impact|what you'll be doing|the work|key duties|duties)", re.I)
NEED_HDR = re.compile(r"(requirement|qualification|what you('| wi)ll (need|bring)|what you bring|what we('re| are) looking for|"
                      r"must[- ]have|about you|you have|who you are|skills|experience you|what we need|you bring|you'll have)", re.I)
INTRO = re.compile(r"\b(you will|you'll|we are looking|we're looking|we are hiring|we're hiring|as a|as our|join)\b", re.I)


def _lines(text):
    return [l.strip(" •-–*·\t") for l in text.split("\n") if l.strip(" •-–*·\t")]


def _clip(s, n):
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) <= n:
        return s
    cut = s[:n]
    end = max(cut.rfind(". "), cut.rfind("; "))
    return (cut[:end + 1] if end > n * 0.5 else cut.rsplit(" ", 1)[0] + "…")


def _is_header(line):
    return len(line) <= 70 and not line.endswith(".") and len(line.split()) <= 9


def _section(lines, hdr, n, width):
    for i, l in enumerate(lines):
        if _is_header(l) and hdr.search(l):
            out = []
            for item in lines[i + 1:]:
                if _is_header(item) and (DO_HDR.search(item) or NEED_HDR.search(item) or ROLE_HDR.search(item)
                                         or re.search(r"benefit|perks|offer|about us|why ", item, re.I)):
                    break
                if len(item) > 25:
                    out.append(_clip(item, width))
                if len(out) >= n:
                    break
            if out:
                return out
    return []


def summarize(job):
    lines = _lines(job.description or "")
    overview = ""
    for i, l in enumerate(lines):
        if _is_header(l) and ROLE_HDR.search(l):
            nxt = next((x for x in lines[i + 1:i + 4] if len(x) > 60), "")
            if nxt:
                overview = nxt
                break
    if not overview:
        overview = next((l for l in lines if len(l) > 60 and INTRO.search(l)), "")
    if not overview:
        overview = next((l for l in lines if len(l) > 60), "")
    return {
        "overview": _clip(overview, 260),
        "do": _section(lines, DO_HDR, 3, 140),
        "need": _section(lines, NEED_HDR, 4, 140),
        "by": "auto",
    }
