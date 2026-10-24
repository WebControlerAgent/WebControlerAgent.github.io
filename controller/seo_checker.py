"""Independent read-only SEO checker using its own endpoint and markup checks.

This intentionally does not call agent_checks.check_seo, so the checker has a
separate implementation from the primary worker. It performs no writes.
"""
from __future__ import annotations

import re
import urllib.error
import urllib.request
from urllib.parse import urljoin, urlparse


def check_seo_independently(base_url: str) -> tuple[bool, str]:
    base = base_url.rstrip("/") + "/"
    parsed = urlparse(base)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False, "Independent checker: invalid HTTP(S) base URL."

    findings: list[str] = []
    evidence: list[str] = []

    def fetch(url: str, limit: int = 150_000) -> tuple[int, str, str]:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "AIWCU-Independent-SEO-Checker/1.0"},
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            body = response.read(limit).decode("utf-8", errors="replace")
            return response.status, response.headers.get("Content-Type", ""), body

    try:
        status, content_type, html = fetch(base)
        title = re.search(r"<title\b[^>]*>(.*?)</title\s*>", html, re.I | re.S)
        description = re.search(
            r"<meta\b[^>]*\bname\s*=\s*['\"]description['\"][^>]*>",
            html, re.I | re.S,
        )
        canonical = re.search(
            r"<link\b[^>]*\brel\s*=\s*['\"]canonical['\"][^>]*>",
            html, re.I | re.S,
        )
        robots = re.search(
            r"<meta\b[^>]*\bname\s*=\s*['\"]robots['\"][^>]*>",
            html, re.I | re.S,
        )
        evidence.append(
            f"checker homepage HTTP {status}; content-type={content_type or 'unknown'}; "
            f"title={'present' if title and title.group(1).strip() else 'missing'}; "
            f"description={'present' if description else 'missing'}; "
            f"canonical={'present' if canonical else 'missing'}; "
            f"robots-meta={'present' if robots else 'not set'}"
        )
        if status < 200 or status >= 300:
            findings.append(f"Homepage HTTP status {status} is not successful.")
        if not title or not title.group(1).strip():
            findings.append("No non-empty HTML title detected.")
        if not description:
            findings.append("Meta description tag not detected.")
        if robots and "noindex" in robots.group(0).lower():
            findings.append("Robots meta includes noindex.")
    except (OSError, urllib.error.URLError, TimeoutError, ValueError) as exc:
        findings.append(f"Homepage fetch failed: {type(exc).__name__}: {exc}")

    robots_text = ""
    sitemap_text = ""
    for endpoint in ("robots.txt", "sitemap.xml"):
        try:
            status, content_type, body = fetch(urljoin(base, endpoint), 100_000)
            evidence.append(f"checker /{endpoint} HTTP {status}; content-type={content_type or 'unknown'}")
            if status < 200 or status >= 300:
                findings.append(f"/{endpoint} did not return a successful HTTP status.")
            elif endpoint == "robots.txt":
                robots_text = body
            else:
                sitemap_text = body
        except (OSError, urllib.error.URLError, TimeoutError, ValueError) as exc:
            findings.append(f"/{endpoint} fetch failed: {type(exc).__name__}: {exc}")

    if robots_text and not re.search(r"(?im)^\s*sitemap\s*:\s*https?://\S+", robots_text):
        findings.append("robots.txt has no absolute Sitemap directive.")
    if sitemap_text:
        if not re.search(r"<(?:urlset|sitemapindex)\b", sitemap_text, re.I):
            findings.append("sitemap.xml does not contain a recognizable sitemap root.")
        locations = re.findall(r"<loc>\s*(https?://[^<\s]+)\s*</loc>", sitemap_text, re.I)
        evidence.append(f"checker absolute sitemap locations={len(locations)}")
        if not locations:
            findings.append("sitemap.xml has no absolute HTTP(S) loc entries.")

    evidence.append("checker findings=" + (" | ".join(findings) if findings else "none detected"))
    return not findings, "; ".join(evidence)
