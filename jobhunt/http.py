"""Small HTTP helper with an on-disk cache, so repeated runs stay polite to job sites."""
import gzip
import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

USER_AGENT = "Mozilla/5.0 (compatible; AhmadJobHunt/1.0; personal job search)"
# Seconds to wait between live requests to the same site (sites that rate-limit hard).
MIN_INTERVAL = {"himalayas.app": 6.0}


class FetchError(Exception):
    def __init__(self, url, status=None, message=""):
        self.url = url
        self.status = status
        super().__init__(f"{status or ''} {message} ({url})".strip())


class Fetcher:
    def __init__(self, cache_dir, cache_hours=6.0, refresh=False, timeout=25):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = cache_hours * 3600
        self.refresh = refresh
        self.timeout = timeout
        self._last = {}
        self.stale = []  # URLs served from an expired cache because the live fetch failed

    def _pace(self, url):
        host = urllib.parse.urlparse(url).netloc
        gap = MIN_INTERVAL.get(host, 0)
        wait = self._last.get(host, 0) + gap - time.time()
        if wait > 0:
            time.sleep(wait)
        self._last[host] = time.time()

    def _cache_path(self, url):
        return self.cache_dir / (hashlib.sha1(url.encode()).hexdigest() + ".cache")

    def get_text(self, url):
        path = self._cache_path(url)
        if not self.refresh and path.exists() and time.time() - path.stat().st_mtime < self.ttl:
            return path.read_text(encoding="utf-8")
        req = urllib.request.Request(url, headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json, application/rss+xml, text/xml, */*",
            "Accept-Encoding": "gzip",
        })
        last = None
        for attempt in range(4):
            self._pace(url)
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    raw = resp.read()
                    if resp.headers.get("Content-Encoding") == "gzip":
                        raw = gzip.decompress(raw)
                    text = raw.decode("utf-8", errors="replace")
                    path.write_text(text, encoding="utf-8")
                    return text
            except urllib.error.HTTPError as e:
                if e.code in (404, 410, 401, 403):
                    raise FetchError(url, e.code, "not available")
                last = FetchError(url, e.code, str(e.reason))
                if e.code == 429:  # rate limited
                    try:
                        delay = float(e.headers.get("Retry-After") or 0) or 15 * (attempt + 1)
                    except ValueError:
                        delay = 15 * (attempt + 1)
                    if delay > 60:  # long lockout: don't sit and wait, use what we have
                        last = FetchError(url, 429, f"rate limited, try again in ~{delay / 60:.0f} min")
                        break
                    time.sleep(delay)
                    continue
            except Exception as e:  # network errors, timeouts
                last = FetchError(url, None, str(e))
            if attempt >= 1:
                break
            time.sleep(2)
        if path.exists():  # live fetch failed: fall back to the last saved copy, however old
            self.stale.append(url)
            return path.read_text(encoding="utf-8")
        raise last

    def get_json(self, url):
        text = self.get_text(url)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            raise FetchError(url, None, "response was not JSON")
