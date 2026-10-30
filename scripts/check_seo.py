"""Fail the Pages build if any localized SEO metadata regresses."""
from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

from seo_postprocess import (SITE_ROOT, LOCALES, HEAD, CANONICAL, LANG_LINK,
                             html_pages, locale_path, post_metadata, read_head_tag)


def require(value, message: str) -> None:
    if not value:
        raise AssertionError(message)


def verify(site: Path) -> None:
    pages = html_pages(site)
    require(len(pages) >= 20, f'Expected populated three-language site, got {len(pages)} pages')
    for (locale, route), file in pages.items():
        text = file.read_text(encoding='utf-8')
        head_match = HEAD.search(text)
        require(head_match is not None, f'Missing head: {file}')
        head = head_match.group(2)
        url = SITE_ROOT + locale_path(locale, route)
        require(read_head_tag(CANONICAL, head) == url, f'Incorrect canonical: {file}')
        require('lang="' + LOCALES[locale][1] + '"' in text.split('<head', 1)[0],
                f'Incorrect document language: {file}')
        links = LANG_LINK.findall(head)
        post = post_metadata(locale, route)
        review = bool(post and post.get('status') == 'review')
        require(len(links) == (0 if review else 4), f'Incorrect hreflang count {len(links)}: {file}')
        if not review:
            for lang in [data[1] for data in LOCALES.values()] + ['x-default']:
                require(len(re.findall('hreflang="' + lang + '"', head)) == 1,
                        f'Missing/duplicate {lang} on {file}')
            for other_locale in LOCALES:
                require(SITE_ROOT + locale_path(other_locale, route) in head,
                        f'Wrong translation destination in {file}')
        for og in ('og:title', 'og:description', 'og:url', 'og:image', 'og:image:width', 'og:image:height', 'og:locale'):
            require(len(re.findall('property="' + og + '"', head)) == 1,
                    f'Missing/duplicate {og}: {file}')
        for twitter in ('twitter:card', 'twitter:title', 'twitter:description', 'twitter:image'):
            require(len(re.findall('name="' + twitter + '"', head)) == 1,
                    f'Missing/duplicate {twitter}: {file}')
        require('content="summary_large_image"' in head, f'Missing Twitter large card {file}')
        require('https://company-notes.com/assets/social/' in head, f'Missing social image {file}')
        json_ld = re.findall(r'<script type="application/ld\+json">(.*?)</script>', head, re.S)
        require(len(json_ld) == (1 if post and not review else 0), f'Bad structured data count {file}')
        if post and not review:
            data = json.loads(json_ld[0]); graph = data['@graph']
            assert data['@context'] == 'https://schema.org'
            assert graph[0]['@type'] == 'BlogPosting'
            assert graph[0]['url'] == url and graph[0]['datePublished']
            if route == 'blog/openwhispr-groq-cloudflare-typeless/':
                assert graph[1]['@type'] == 'VideoObject'
                assert graph[1]['contentUrl'].endswith('My_Typeless.mp4')
                assert graph[1]['thumbnailUrl'].endswith('My_Typeless_poster.jpg')
                assert graph[1]['duration'] == 'PT10S'
        if review:
            require('name="robots" content="noindex, follow"' in head,
                    f'Review must remain noindex: {file}')
    for name in ('company-notes','field-notes','playbooks','toolkit'):
        image = site / 'assets/social' / (name + '.png')
        require(image.is_file() and image.read_bytes().startswith(b'\x89PNG'),
                f'Missing valid PNG social card: {image}')
    ns = '{http://www.sitemaps.org/schemas/sitemap/0.9}'
    for locale, (prefix, _, _) in LOCALES.items():
        sitemap = site / prefix / 'sitemap.xml'
        entries = ET.parse(sitemap).getroot()
        urls = [e.find(ns + 'loc').text for e in entries]
        expected = {SITE_ROOT + locale_path(loc, route) for (loc, route) in pages
                    if loc == locale and not (post_metadata(loc, route) or {}).get('status') == 'review'}
        require(set(urls) == expected,
                f'Sitemap indexable URLs differ for {locale}: missing={expected-set(urls)}, extra={set(urls)-expected}')
        for entry in entries:
            url = entry.find(ns + 'loc').text
            route = url[len(SITE_ROOT + locale_path(locale,'')):]
            info = post_metadata(locale, route)
            require(not info or info.get('status') != 'review', f'Noindex page in sitemap: {url}')
            lastmod = entry.find(ns + 'lastmod')
            if lastmod is not None:
                d = date.fromisoformat(lastmod.text)
                require(d <= date.today(), f'Future lastmod in {sitemap}')
        require(any('/blog/openwhispr-groq-cloudflare-typeless/' in u for u in urls),
                f'Missing published OpenWhispr article in {sitemap}')
    print(f'SEO audit PASSED: {len(pages)} pages, three clean sitemaps, 4 social images, video metadata.')


if __name__ == '__main__':
    verify(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / 'site')
