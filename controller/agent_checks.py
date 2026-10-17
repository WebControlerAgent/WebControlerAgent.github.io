"""Read-only health checks used by the GitHub-native agent runtime."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path


def http_json(url: str, timeout: int = 15):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "WebControlerAgent/1.0"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.status, response.read()


def check_target_repo(repository: str) -> tuple[bool, str]:
    if not repository or "/" not in repository:
        return False, "Target repository is missing or malformed."
    try:
        status, body = http_json(f"https://api.github.com/repos/{repository}")
        data = json.loads(body.decode("utf-8"))
        if status != 200:
            return False, f"GitHub repository returned HTTP {status}."
        return True, f"Repository reachable: {data.get('full_name', repository)}."
    except Exception as exc:
        return False, f"Repository check failed: {exc}"


def check_live_site(url: str) -> tuple[bool, str]:
    if not url:
        return False, "Live URL is not configured."
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "WebControlerAgent/1.0"},
        )
        with urllib.request.urlopen(req, timeout=20) as response:
            code = response.status
            content_type = response.headers.get("content-type", "")
        if code < 200 or code >= 400:
            return False, f"Live site returned HTTP {code}."
        return True, f"Live site reachable: HTTP {code} ({content_type or 'unknown content type'})."
    except urllib.error.HTTPError as exc:
        return False, f"Live site returned HTTP {exc.code}."
    except Exception as exc:
        return False, f"Live site check failed: {exc}"


def check_seo(url: str) -> tuple[bool, str]:
    """Inspect only the authorized homepage plus robots.txt and sitemap.xml.

    This is a read-only technical SEO audit, not a Google indexing/ranking test.
    """
    import re
    from urllib.parse import urljoin, urlparse

    base = url.rstrip("/") + "/"
    parsed = urlparse(base)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return False, "Live URL must be a valid HTTP(S) URL."
    checks = []
    failures = []

    def fetch_text(target: str, limit: int = 200_000):
        req = urllib.request.Request(
            target,
            headers={"User-Agent": "WebControlerAgent/1.1 (+read-only SEO audit)"},
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            status = response.status
            content_type = response.headers.get("content-type", "")
            body = response.read(limit).decode("utf-8", errors="ignore")
        return status, content_type, body

    # Homepage technical metadata: do not crawl or follow arbitrary page links.
    try:
        code, content_type, html = fetch_text(base)
        title_match = re.search(r"<title\b[^>]*>(.*?)</title\s*>", html, re.I | re.S)
        description_match = re.search(
            r"<meta\b(?=[^>]*\bname\s*=\s*['\"]description['\"])[^>]*\bcontent\s*=\s*['\"]([^'\"]*)['\"][^>]*>",
            html, re.I | re.S,
        )
        canonical_match = re.search(
            r"<link\b(?=[^>]*\brel\s*=\s*['\"]canonical['\"])[^>]*\bhref\s*=\s*['\"]([^'\"]+)['\"][^>]*>",
            html, re.I | re.S,
        )
        robots_match = re.search(
            r"<meta\b(?=[^>]*\bname\s*=\s*['\"]robots['\"])[^>]*\bcontent\s*=\s*['\"]([^'\"]*)['\"][^>]*>",
            html, re.I | re.S,
        )
        title = re.sub(r"\s+", " ", title_match.group(1)).strip() if title_match else ""
        description = re.sub(r"\s+", " ", description_match.group(1)).strip() if description_match else ""
        canonical = urljoin(base, canonical_match.group(1).strip()) if canonical_match else ""
        robots_meta = robots_match.group(1).strip().lower() if robots_match else ""
        checks.append(
            f"homepage: HTTP {code}; content-type={content_type or 'unknown'}; "
            f"title={'present' if title else 'MISSING'} ({len(title)} chars); "
            f"meta-description={'present' if description else 'MISSING'} ({len(description)} chars); "
            f"canonical={'present' if canonical else 'MISSING'}; "
            f"robots-meta={robots_meta or 'not set'}"
        )
        if not 200 <= code < 300:
            failures.append(f"Homepage returned HTTP {code}")
        if not title:
            failures.append("Homepage has no detectable <title>")
        if not description:
            failures.append("Homepage has no detectable meta description")
        if "noindex" in robots_meta:
            failures.append("Homepage robots meta contains noindex")
        if canonical and urlparse(canonical).scheme not in ("http", "https"):
            failures.append("Homepage canonical URL is not HTTP(S)")
    except Exception as exc:
        failures.append(f"homepage: {type(exc).__name__}: {exc}")

    # robots.txt and sitemap.xml endpoint checks.
    robots_body = ""
    sitemap_body = ""
    for path in ("robots.txt", "sitemap.xml"):
        try:
            code, content_type, body = fetch_text(urljoin(base, path), limit=100_000)
            checks.append(f"/{path}: HTTP {code}; content-type={content_type or 'unknown'}; bytes-read={len(body.encode('utf-8'))}")
            if not 200 <= code < 300:
                failures.append(f"/{path} returned HTTP {code}")
            elif path == "robots.txt":
                robots_body = body
                if not body.strip():
                    failures.append("/robots.txt is empty")
            else:
                sitemap_body = body
                if "<urlset" not in body.lower() and "<sitemapindex" not in body.lower():
                    failures.append("/sitemap.xml does not look like XML sitemap content")
                elif not re.search(r"<loc>\s*https?://", body, re.I):
                    failures.append("/sitemap.xml has no detectable absolute HTTP(S) <loc> entry")
        except Exception as exc:
            failures.append(f"/{path}: {type(exc).__name__}: {exc}")

    if robots_body:
        sitemap_refs = re.findall(r"(?im)^\s*sitemap\s*:\s*(\S+)", robots_body)
        checks.append(f"robots-sitemap-directive={'present' if sitemap_refs else 'not present'}")
        if not sitemap_refs:
            failures.append("/robots.txt does not declare a Sitemap URL")
    if sitemap_body:
        loc_count = len(re.findall(r"<loc>\s*https?://", sitemap_body, re.I))
        checks.append(f"sitemap-absolute-loc-count={loc_count}")
    if failures:
        return False, "; ".join(checks + ["findings=" + " | ".join(failures)])
    return True, "; ".join(checks + ["findings=none detected"])


def run_checks(site: dict, agent: str) -> tuple[bool, str]:
    if agent == "researcher":
        return check_target_repo(str(site.get("repository", "")))
    if agent == "publisher":
        return check_target_repo(str(site.get("repository", "")))
    if agent == "seo-agent":
        return check_seo(str(site.get("live_url", "")))
    if agent == "qa":
        live_ok, live_detail = check_live_site(str(site.get("live_url", "")))
        if not live_ok:
            return False, live_detail
        seo_ok, seo_detail = check_seo(str(site.get("live_url", "")))
        if not seo_ok:
            return False, seo_detail
        return True, f"{live_detail} {seo_detail}"
    return True, "No external check required for this stage."
