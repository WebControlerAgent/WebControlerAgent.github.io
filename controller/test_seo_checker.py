"""Unit tests for independent SEO metadata and sitemap quality checks."""
import unittest

from controller.seo_checker import inspect_homepage_metadata, inspect_sitemap


class SeoCheckerValidationTests(unittest.TestCase):
    def test_accepts_valid_metadata(self):
        html = """
        <html><head>
        <title>Example Site</title>
        <meta content="A useful description." name="description">
        <link href="https://example.com/" rel="canonical">
        <meta name="robots" content="index, follow">
        </head></html>
        """
        evidence, findings = inspect_homepage_metadata(html, "https://example.com/")
        self.assertTrue(any("meta-description=present" in item for item in evidence))
        self.assertEqual(findings, [])

    def test_rejects_empty_description(self):
        _, findings = inspect_homepage_metadata(
            '<title>Example</title><meta name="description" content="">'
            '<link rel="canonical" href="https://example.com/">',
            "https://example.com/",
        )
        self.assertIn("Homepage meta description is missing or empty.", findings)

    def test_rejects_cross_host_canonical(self):
        _, findings = inspect_homepage_metadata(
            '<title>Example</title><meta name="description" content="Description">'
            '<link rel="canonical" href="https://other.example/page">',
            "https://example.com/",
        )
        self.assertIn("Canonical URL host differs from the audited site's host.", findings)

    def test_rejects_noindex(self):
        _, findings = inspect_homepage_metadata(
            '<title>Example</title><meta name="description" content="Description">'
            '<link rel="canonical" href="https://example.com/">'
            '<meta name="robots" content="noindex, follow">',
            "https://example.com/",
        )
        self.assertIn("Homepage robots meta contains noindex.", findings)

    def test_rejects_duplicate_sitemap_urls(self):
        sitemap = """<urlset><url><loc>https://example.com/</loc></url>
        <url><loc>https://example.com/</loc></url></urlset>"""
        _, findings = inspect_sitemap(sitemap, "https://example.com/")
        self.assertTrue(any("duplicate loc URL" in item for item in findings))

    def test_rejects_sitemap_urls_on_other_host(self):
        _, findings = inspect_sitemap(
            "<urlset><url><loc>https://other.example/page</loc></url></urlset>",
            "https://example.com/",
        )
        self.assertTrue(any("different host" in item for item in findings))

    def test_rejects_invalid_xml(self):
        _, findings = inspect_sitemap("<urlset><url>", "https://example.com/")
        self.assertIn("sitemap.xml is not well-formed XML.", findings)

    def test_accepts_valid_sitemap(self):
        evidence, findings = inspect_sitemap(
            "<urlset><url><loc>https://example.com/</loc></url>"
            "<url><loc>https://example.com/chapter.html</loc></url></urlset>",
            "https://example.com/",
        )
        self.assertTrue(any("absolute sitemap locations=2" in item for item in evidence))
        self.assertEqual(findings, [])


if __name__ == "__main__":
    unittest.main()
