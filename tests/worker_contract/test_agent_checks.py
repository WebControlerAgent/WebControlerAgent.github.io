"""Unit tests for the deterministic, read-only site health worker."""
import unittest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

from controller.agent_checks import check_live_site, check_seo, run_checks


def response(status=200, body=b"<urlset></urlset>", content_type="text/html"):
    item = MagicMock()
    item.status = status
    item.headers = {"content-type": content_type}
    item.read.return_value = body
    item.__enter__.return_value = item
    item.__exit__.return_value = False
    return item


HOME_HTML = b'<html><head><title>Example</title><meta name="description" content="Example site"></head></html>'
ROBOTS = b"User-agent: *\nAllow: /\nSitemap: https://example.test/sitemap.xml"


class AgentChecksTests(unittest.TestCase):
    @patch("controller.agent_checks.urllib.request.urlopen")
    def test_live_site_reports_http_and_content_type(self, urlopen):
        urlopen.return_value = response(200, content_type="text/html")
        ok, detail = check_live_site("https://example.test/")
        self.assertTrue(ok)
        self.assertIn("HTTP 200", detail)
        self.assertIn("text/html", detail)

    @patch("controller.agent_checks.urllib.request.urlopen")
    def test_live_site_reports_http_error(self, urlopen):
        urlopen.side_effect = HTTPError("https://example.test/", 503, "Unavailable", {}, None)
        ok, detail = check_live_site("https://example.test/")
        self.assertFalse(ok)
        self.assertIn("HTTP 503", detail)

    @patch("controller.agent_checks.urllib.request.urlopen")
    def test_seo_requires_a_valid_sitemap_document(self, urlopen):
        urlopen.side_effect = [
            response(body=HOME_HTML),
            response(body=ROBOTS),
            response(body=b"not xml", content_type="application/xml"),
        ]
        ok, detail = check_seo("https://example.test/")
        self.assertFalse(ok)
        self.assertIn("does not look like XML sitemap content", detail)

    @patch("controller.agent_checks.urllib.request.urlopen")
    def test_seo_passes_robots_and_sitemap(self, urlopen):
        urlopen.side_effect = [
            response(body=HOME_HTML),
            response(body=ROBOTS),
            response(
                body=b"<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'><url><loc>https://example.test/</loc></url></urlset>",
                content_type="application/xml",
            ),
        ]
        ok, detail = check_seo("https://example.test/")
        self.assertTrue(ok)
        self.assertIn("/robots.txt: HTTP 200", detail)
        self.assertIn("/sitemap.xml: HTTP 200", detail)
        self.assertIn("sitemap-absolute-loc-count=1", detail)

    @patch("controller.agent_checks.check_seo", return_value=(True, "SEO checks passed"))
    @patch("controller.agent_checks.check_live_site", return_value=(True, "Site reachable"))
    def test_qa_runs_live_and_seo_checks(self, live, seo):
        ok, detail = run_checks({"live_url": "https://example.test/"}, "qa")
        self.assertTrue(ok)
        live.assert_called_once()
        seo.assert_called_once()
        self.assertIn("Site reachable", detail)
        self.assertIn("SEO checks passed", detail)


if __name__ == "__main__":
    unittest.main()
