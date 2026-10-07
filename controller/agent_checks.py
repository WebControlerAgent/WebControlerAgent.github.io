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
    base = url.rstrip("/")
    checks = []
    failures = []
    for path in ("/robots.txt", "/sitemap.xml"):
        try:
            req = urllib.request.Request(
                base + path,
                headers={"User-Agent": "WebControlerAgent/1.0"},
            )
            with urllib.request.urlopen(req, timeout=15) as response:
                code = response.status
                body = response.read(2000).decode("utf-8", errors="ignore")
            checks.append(f"{path}: HTTP {code}")
            if code >= 400:
                failures.append(f"{path} returned HTTP {code}")
            elif path == "/sitemap.xml" and "<urlset" not in body and "<sitemapindex" not in body:
                failures.append("sitemap.xml does not look like a sitemap document")
        except Exception as exc:
            failures.append(f"{path}: {exc}")
    if failures:
        return False, "; ".join(failures)
    return True, "; ".join(checks)


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
