"""Independent read-only SEO checker using its own endpoint and markup checks.

This intentionally does not call agent_checks.check_seo. It validates metadata
values and sitemap URL quality without crawling arbitrary page links or writing.
"""
from __future__ import annotations

import re
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse


class _MetadataParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.in_title = False
        self.meta: dict[str, list[dict[str, str]]] = {}
        self.links: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {str(k).lower(): (v or "").strip() for k, v in attrs}
        if tag.lower() == "title":
            self.in_title = True
        elif tag.lower() == "meta":
            name = values.get("name", "").lower()
            if name:
                self.meta.setdefault(name, []).append(values)
        elif tag.lower() == "link":
            self.links.append(values)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)


def inspect_homepage_metadata(html: str, base_url: str) -> tuple[list[str], list[str]]:
    """Return evidence and findings for title, description, canonical and robots."""
    parser = _MetadataParser()
    parser.feed(html)
    title = re.sub(r"\s+", " ", "".join(parser.title_parts)).strip()
    descriptions = parser.meta.get("description", [])
    description = next((m.get("content", "").strip() for m in descriptions if m.get("content", "").strip()), "")
    canonicals = [link.get("href", "").strip() for link in parser.links
                  if "canonical" in link.get("rel", "").lower().split()]
    canonical_raw = next((value for value in canonicals if value), "")
    canonical = urljoin(base_url, canonical_raw) if canonical_raw else ""
    robots = " | ".join(m.get("content", "") for m in parser.meta.get("robots", []))
    base_host = (urlparse(base_url).hostname or "").lower()
    canonical_parts = urlparse(canonical) if canonical else None

    evidence = [
        f"title={'present' if title else 'missing'} ({len(title)} chars)",
        f"meta-description={'present' if description else 'missing'} ({len(description)} chars)",
        f"canonical={'present' if canonical else 'missing'}",
        f"robots-meta={robots.lower() or 'not set'}",
    ]
    findings: list[str] = []
    if not title:
        findings.append("Homepage has no non-empty title.")
    if not description:
        findings.append("Homepage meta description is missing or empty.")
    if not canonical:
        findings.append("Homepage canonical link is missing or empty.")
    elif canonical_parts.scheme not in {"http", "https"} or not canonical_parts.netloc:
        findings.append("Canonical URL is not a valid absolute HTTP(S) URL.")
    elif (canonical_parts.hostname or "").lower() != base_host:
        findings.append("Canonical URL host differs from the audited site's host.")
    if "noindex" in robots.lower():
        findings.append("Homepage robots meta contains noindex.")
    return evidence, findings


def inspect_sitemap(sitemap_text: str, base_url: str) -> tuple[list[str], list[str]]:
    """Check sitemap XML, absolute HTTP(S) locations, duplicates and host alignment."""
    evidence: list[str] = []
    findings: list[str] = []
    try:
        root = ET.fromstring(sitemap_text)
    except ET.ParseError as exc:
        return [f"sitemap XML parse failed: {exc}"], ["sitemap.xml is not well-formed XML."]
    root_name = root.tag.rsplit("}", 1)[-1].lower()
    if root_name not in {"urlset", "sitemapindex"}:
        findings.append("sitemap.xml root must be urlset or sitemapindex.")
    locs = [node.text.strip() for node in root.iter()
            if node.tag.rsplit("}", 1)[-1].lower() == "loc" and node.text and node.text.strip()]
    evidence.append(f"absolute sitemap locations={sum(1 for value in locs if urlparse(value).scheme in {'http', 'https'} and urlparse(value).netloc)}")
    if not locs:
        findings.append("sitemap.xml has no non-empty loc entries.")
    seen: set[str] = set()
    duplicates: list[str] = []
    off_host: list[str] = []
    invalid: list[str] = []
    base_host = (urlparse(base_url).hostname or "").lower()
    for value in locs:
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            invalid.append(value)
            continue
        normalized = value.rstrip("/")
        if normalized in seen:
            duplicates.append(value)
        seen.add(normalized)
        if (parsed.hostname or "").lower() != base_host:
            off_host.append(value)
    if invalid:
        findings.append(f"Sitemap has {len(invalid)} non-absolute or non-HTTP(S) loc URL(s).")
    if duplicates:
        findings.append(f"Sitemap contains {len(duplicates)} duplicate loc URL(s).")
    if off_host:
        findings.append(f"Sitemap contains {len(off_host)} URL(s) on a different host.")
    return evidence, findings


def check_seo_independently(base_url: str) -> tuple[bool, str]:
    base = base_url.rstrip("/") + "/"
    parsed = urlparse(base)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False, "Independent checker: invalid HTTP(S) base URL."
    findings: list[str] = []
    evidence: list[str] = []

    def fetch(url: str, limit: int = 150_000) -> tuple[int, str, str]:
        req = urllib.request.Request(url, headers={"User-Agent": "AIWCU-Independent-SEO-Checker/2.0"})
        with urllib.request.urlopen(req, timeout=15) as response:
            body = response.read(limit).decode("utf-8", errors="replace")
            return response.status, response.headers.get("Content-Type", ""), body

    try:
        status, content_type, html = fetch(base)
        metadata_evidence, metadata_findings = inspect_homepage_metadata(html, base)
        evidence.append(
            f"checker homepage HTTP {status}; content-type={content_type or 'unknown'}; "
            + "; ".join(metadata_evidence)
        )
        findings.extend(metadata_findings)
        if status < 200 or status >= 300:
            findings.append(f"Homepage HTTP status {status} is not successful.")
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
        sitemap_evidence, sitemap_findings = inspect_sitemap(sitemap_text, base)
        evidence.extend(sitemap_evidence)
        findings.extend(sitemap_findings)

    evidence.append("checker findings=" + (" | ".join(findings) if findings else "none detected"))
    return not findings, "; ".join(evidence)
