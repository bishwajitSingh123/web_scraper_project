# fetcher.py
import requests
import time
import hashlib
import os
import csv
import urllib.parse
from urllib import robotparser
from datetime import datetime

# Configuration
RATE_DELAY = 1.0          # seconds to sleep between requests (simple rate limiter)
DEFAULT_HEADERS = {
    "User-Agent": "web-scraper-batch/1.0 (+https://example.com/contact)"
}
LOG_PATH = os.path.join("logs", "run_log.csv")
RAW_DIR = "raw_pages"
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

# Robots cache to avoid reloading robots.txt repeatedly
_ROBOTS_CACHE = {}

def _url_to_filename(url: str) -> str:
    """Create a deterministic filename for a URL using SHA1 hash."""
    h = hashlib.sha1(url.encode("utf-8")).hexdigest()
    return f"{h}.html"

def save_raw_html(url: str, html: str) -> str:
    """Save HTML to raw_pages/<sha1>.html and return filename."""
    filename = _url_to_filename(url)
    path = os.path.join(RAW_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path

def is_allowed(url: str, user_agent: str = DEFAULT_HEADERS["User-Agent"]) -> bool:
    """Check robots.txt for permission to fetch url."""
    parsed = urllib.parse.urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    rp = _ROBOTS_CACHE.get(base)
    if rp is None:
        robots_url = urllib.parse.urljoin(base, "/robots.txt")
        rp = robotparser.RobotFileParser()
        try:
            rp.set_url(robots_url)
            rp.read()
        except Exception:
            # If robots can't be fetched or parsed, be conservative and allow
            # (alternatively, choose to block). We log potential issues externally.
            rp = None
        _ROBOTS_CACHE[base] = rp

    if rp is None:
        # No robots parser available -> allow by default (you can change to False)
        return True
    return rp.can_fetch(user_agent, url)

def fetch_url(url: str, timeout: int = 15, headers: dict = None) -> tuple:
    """
    Perform a single GET request.
    Returns: (status_code:int, text:str, latency:float, error:str or None)
    """
    headers = headers or DEFAULT_HEADERS
    start = time.time()
    try:
        r = requests.get(url, headers=headers, timeout=timeout)
        latency = time.time() - start
        return r.status_code, r.text, latency, None
    except requests.RequestException as e:
        latency = time.time() - start
        return None, None, latency, str(e)

def fetch_with_retries(url: str, retries: int = 3, backoff: float = 2.0, rate_delay: float = RATE_DELAY):
    """
    Fetch with retries and simple exponential backoff.
    Writes an entry to LOG_PATH for each URL (success or failure).
    Returns path to saved file on success, or None on failure.
    """
    # Respect robots.txt
    allowed = is_allowed(url)
    if not allowed:
        _log(url, None, 0.0, 0, None, error="blocked_by_robots")
        return None

    attempt = 0
    err = None
    while attempt <= retries:
        if attempt > 0:
            # exponential backoff before retry
            sleep_time = backoff ** (attempt - 1)
            time.sleep(sleep_time)

        # rate limiting between attempts/requests
        time.sleep(rate_delay)

        status, text, latency, error = fetch_url(url)
        if status is not None and 200 <= status < 400 and text:
            # success
            filepath = save_raw_html(url, text)
            _log(url, status, latency, attempt, filepath, None)
            return filepath
        else:
            err = error or f"status_{status}"
            attempt += 1

    # all retries exhausted
    _log(url, status, latency, retries, None, err)
    return None

def _log(url, status_code, latency_s, retries, filename, error):
    """Append run log CSV row (timestamp,url,status_code,latency_s,retries,filename,error)"""
    ts = datetime.utcnow().isoformat()
    header_needed = not os.path.exists(LOG_PATH) or os.path.getsize(LOG_PATH) == 0
    with open(LOG_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if header_needed:
            writer.writerow(["timestamp", "url", "status_code", "latency_s", "retries", "filename", "error"])
        writer.writerow([ts, url, status_code, f"{latency_s:.3f}" if latency_s is not None else "", retries, filename or "", error or ""])
