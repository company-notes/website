"""Ensure SEO enrichment cannot reflow or replace page content."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from seo_postprocess import HEAD, update_head


class SEOHeadOnlyTests(unittest.TestCase):
    def test_head_metadata_keeps_visible_body_unchanged_and_language_targets_correct(self):
        canonical = "https://company-notes.com/zh-hans/"
        raw = (
            '<!doctype html>\n<html lang="zh" class="no-js"><head>'
            '<meta name="description" content="Short intro.">'
            '<link rel="canonical" href="' + canonical + '">'
            '<link rel="alternate" href="/" hreflang="zh-Hant">'
            '<link rel="alternate" href="/en/" hreflang="en">'
            '<link rel="alternate" href="/zh-hans/" hreflang="zh-Hans">'
            '<title>Company Notes - Company Notes</title></head>'
            '<body><main><h1>Text unchanged</h1><p>Visible content.</p></main></body></html>'
        )
        pages = {(locale, ''): Path(locale) for locale in ('zh-hant', 'en', 'zh-hans')}
        output = update_head(raw, locale='zh-hans', route='', pages=pages)
        self.assertEqual(output.split('<body', 1)[1], raw.split('<body', 1)[1])
        self.assertIn('<html lang="zh-Hans"', output)
        head = HEAD.search(output).group(2)
        self.assertEqual(head.count('rel="alternate"'), 4)
        self.assertIn('href="https://company-notes.com/en/"', head)
        self.assertIn('href="https://company-notes.com/"', head)
        self.assertIn('href="https://company-notes.com/zh-hans/"', head)
        self.assertNotIn('rel="alternate" href="/en/"', head)
        self.assertIn('property="og:image"', head)
        self.assertIn('name="twitter:card"', head)


if __name__ == "__main__":
    unittest.main()
