"""Add metadata to the compiled Pages site without touching visible article content.

MkDocs Material's extra.alternate entries are needed for the visible language
selector, but are also copied into <head> pointing to the *homepages* on every
article. Rewrite just the head of each built HTML file instead of removing that
selector. Leave the page body byte-for-byte unchanged.
"""
from __future__ import annotations

from datetime import date
from html import escape, unescape
from pathlib import Path
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

import yaml
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SITE_ROOT = 'https://company-notes.com'
LOCALES = {'zh-hant': ('', 'zh-Hant', 'zh_TW'),
           'en': ('en', 'en', 'en_US'),
           'zh-hans': ('zh-hans', 'zh-Hans', 'zh_CN')}
CATEGORIES = {'Field Notes': 'field-notes', 'Playbooks': 'playbooks', 'Toolkit': 'toolkit'}
VIDEO_SLUG = 'openwhispr-groq-cloudflare-typeless'
VIDEO_NAMES = {'zh-hant': 'OpenWhispr 語音輸入：最後的成果',
               'en': 'OpenWhispr dictation: The final result',
               'zh-hans': 'OpenWhispr 语音输入：最终成果'}

# All changes are restricted to <head> and, for zh-Hans, the root html lang.
HEAD = re.compile(r'(<head\b[^>]*>)(.*?)(</head\s*>)', re.I | re.S)
LANG_LINK = re.compile(r'[ \t]*<link\b[^>]*\brel=["\']alternate["\'][^>]*\bhreflang=["\'][^"\']+["\'][^>]*>\s*', re.I)
META = re.compile(r'<meta\s+name=["\'](?P<name>[^"\']+)["\']\s+content=["\'](?P<content>[^"\']*)["\']', re.I)
TITLE = re.compile(r'<title>(.*?)</title>', re.I | re.S)
CANONICAL = re.compile(r'<link\s+rel=["\']canonical["\']\s+href=["\']([^"\']+)', re.I)


def locale_path(locale: str, route: str) -> str:
    prefix = LOCALES[locale][0]
    return '/' + (prefix + '/' if prefix else '') + route


def page_source(locale: str, route: str) -> Path | None:
    """Locate an original content file for a durable last-modified date."""
    source_dir = ROOT / 'content' / locale
    if route.startswith('blog/') and route.count('/') == 2 and route.endswith('/'):
        slug = route.split('/')[1]
        candidates = list((source_dir / 'blog/posts').glob(f'*-{slug}.md'))
        return candidates[0] if len(candidates) == 1 else None
    static_routes = {'about/': 'about.md', 'playbooks/organization/': 'playbooks/organization.md',
                     'playbooks/daily-operations/': 'playbooks/daily-operations.md'}
    path = source_dir / static_routes[route] if route in static_routes else None
    return path if path and path.is_file() else None


def last_mod(path: Path) -> str | None:
    """Use the source's real Git commit date, never the build timestamp."""
    try:
        rel = path.relative_to(ROOT)
        result = subprocess.run(['git', '-C', str(ROOT), 'log', '-1', '--format=%cs', '--', str(rel)],
                                capture_output=True, text=True, timeout=15, check=True)
        raw = result.stdout.strip()
        return date.fromisoformat(raw).isoformat() if raw else None
    except (ValueError, OSError, subprocess.SubprocessError):
        return None


def post_metadata(locale: str, route: str) -> dict | None:
    source = page_source(locale, route)
    if not source or '/blog/posts/' not in source.as_posix():
        return None
    body = source.read_text(encoding='utf-8')
    if not body.startswith('---\n'):
        raise ValueError(f'Missing front matter in {source}')
    data = yaml.safe_load(body.split('---\n', 2)[1])
    if data.get('slug') != route.split('/')[1]:
        raise ValueError(f'Slug mismatch: {source}')
    return data


def html_pages(site: Path) -> dict[tuple[str, str], Path]:
    pages = {}
    for locale, (prefix, _, _) in LOCALES.items():
        directory = site / prefix
        for page in directory.rglob('index.html'):
            # The default locale lives at site/, so skip the nested locales.
            rel = page.relative_to(directory).as_posix()
            if not prefix and rel.startswith(('en/', 'zh-hans/')):
                continue
            route = '' if rel == 'index.html' else rel.removesuffix('index.html')
            pages[locale, route] = page
    return pages


def read_head_tag(pattern: re.Pattern, head: str, default: str = '') -> str:
    match = pattern.search(head)
    return unescape(match.group(1).strip()) if match else default


def description(head: str) -> str:
    for m in META.finditer(head):
        if m.group('name').lower() == 'description':
            return unescape(m.group('content'))
    return ''


def render_cards(site: Path) -> None:
    """Generate metadata-only, 1200x630 PNGs with an OS-available font."""
    target = site / 'assets/social'
    target.mkdir(parents=True, exist_ok=True)
    cards = {
        'company-notes': ('#BDEAD8', '#183A37', 'COMPANY NOTES'),
        'field-notes': ('#92D3C5', '#173E39', 'FIELD NOTES'),
        'playbooks': ('#EDDC96', '#323F4B', 'PLAYBOOKS'),
        'toolkit': ('#A2C4F3', '#193E70', 'TOOLKIT'),
    }
    fonts = ['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
             '/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf']
    fontpath = next((f for f in fonts if Path(f).is_file()), None)
    large = ImageFont.truetype(fontpath, 90) if fontpath else ImageFont.load_default()
    mid = ImageFont.truetype(fontpath, 46) if fontpath else ImageFont.load_default()
    small = ImageFont.truetype(fontpath, 24) if fontpath else ImageFont.load_default()
    for key, (bg, ink, label) in cards.items():
        img = Image.new('RGB', (1200, 630), bg)
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((62, 56, 1138, 574), radius=35, outline=ink, width=6)
        d.rounded_rectangle((95, 94, 189, 188), radius=25, fill=ink)
        for y, width in [(121, 62), (143, 45), (165, 62)]:
            d.rounded_rectangle((110, y, 110 + width, y + 6), radius=3, fill=bg)
        d.text((218, 104), 'COMPANY NOTES', font=mid, fill=ink)
        d.line((98, 230, 1099, 230), fill=ink, width=5)
        d.text((95, 295), label, font=large, fill=ink, stroke_width=0)
        d.text((101, 510), 'REAL NOTES ON WORKING WITH AI', font=small, fill=ink)
        img.save(target / f'{key}.png', format='PNG', optimize=True)


def update_head(html: str, *, locale: str, route: str, pages: dict[tuple[str, str], Path]) -> str:
    match = HEAD.search(html)
    if not match:
        raise ValueError(f'No HTML head for {locale}/{route}')
    old_head = match.group(2)
    canonical = read_head_tag(CANONICAL, old_head)
    expected_url = SITE_ROOT + locale_path(locale, route)
    if canonical != expected_url:
        raise ValueError(f'Unexpected canonical {canonical} != {expected_url}')
    title = read_head_tag(TITLE, old_head)
    desc = description(old_head)
    if not title or not desc:
        raise ValueError(f'Missing original title/description: {locale}/{route}')
    info = post_metadata(locale, route)
    is_review = bool(info and info.get('status') == 'review')
    category = (info.get('categories') or [''])[0] if info else ''
    cover = CATEGORIES.get(category, 'company-notes')
    if is_review:
        # No hreflang declarations for deliberately unindexed articles.
        alternatives = []
    else:
        alternatives = [
            f'<link rel="alternate" hreflang="{lang}" href="{escape(SITE_ROOT + locale_path(loc, route), quote=True)}">'
            for loc, (_, lang, _) in LOCALES.items() if (loc, route) in pages
        ]
        if ('zh-hant', route) in pages:
            alternatives.append('<link rel="alternate" hreflang="x-default" href="'
                                + escape(SITE_ROOT + locale_path('zh-hant', route), quote=True) + '">')
    image = SITE_ROOT + '/assets/social/' + cover + '.png'
    lang_value = LOCALES[locale][1]
    og_title = info.get('title') if info else title.removesuffix(' - Company Notes')
    tags = [
        f'<meta property="og:title" content="{escape(str(og_title), quote=True)}">',
        f'<meta property="og:description" content="{escape(desc, quote=True)}">',
        f'<meta property="og:url" content="{escape(canonical, quote=True)}">',
        f'<meta property="og:image" content="{escape(image, quote=True)}">',
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        '<meta property="og:image:type" content="image/png">',
        f'<meta property="og:locale" content="{LOCALES[locale][2]}">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{escape(str(og_title), quote=True)}">',
        f'<meta name="twitter:description" content="{escape(desc, quote=True)}">',
        f'<meta name="twitter:image" content="{escape(image, quote=True)}">',
    ]
    if info and not is_review:
        data = {
            '@type': 'BlogPosting', 'headline': info['title'], 'description': desc,
            'mainEntityOfPage': {'@type': 'WebPage', '@id': canonical},
            'url': canonical, 'inLanguage': lang_value,
            'datePublished': str(info['date']), 'author': {'@type': 'Organization', 'name': 'Company Notes'},
            'publisher': {'@type': 'Organization', 'name': 'Company Notes', 'url': SITE_ROOT + '/'},
            'image': [image],
        }
        source = page_source(locale, route)
        modified = last_mod(source) if source else None
        if modified:
            data['dateModified'] = modified
        graph = [data]
        if route == 'blog/' + VIDEO_SLUG + '/':
            v = {
                '@type': 'VideoObject', 'name': VIDEO_NAMES[locale],
                'description': desc, 'inLanguage': lang_value,
                'thumbnailUrl': SITE_ROOT + locale_path(locale, 'assets/posts/openwhispr-typeless/My_Typeless_poster.jpg'),
                'contentUrl': SITE_ROOT + locale_path(locale, 'assets/posts/openwhispr-typeless/My_Typeless.mp4'),
                'uploadDate': str(info['date']), 'duration': 'PT10S',
                'width': 832, 'height': 710,
                'isPartOf': {'@id': canonical},
            }
            graph.append(v)
        structured = {'@context': 'https://schema.org', '@graph': graph}
        encoded = json.dumps(structured, ensure_ascii=False).replace('<', '\\u003c')
        tags.append('<script type="application/ld+json">' + encoded + '</script>')
    # The original Material auto-tags point to homepages, even on articles.
    # Strip all hreflang head links and emit exactly one per actual translation.
    clean_head = LANG_LINK.sub('', old_head)
    addition = '\n    ' + '\n    '.join(alternatives + tags) + '\n  '
    new_head = clean_head + addition
    output = html[:match.start(2)] + new_head + html[match.end(2):]
    if locale == 'zh-hans':
        output, changed = re.subn(r'(<html\s+lang=["\'])zh(["\'])', r'\1zh-Hans\2', output, count=1)
        if changed != 1:
            raise ValueError('Expected zh-Hans html language normalization')
    # The only edits should be in <head> and the root html lang attribute.
    before_body = html.split('<body', 1)[1]
    after_body = output.split('<body', 1)[1]
    if before_body != after_body:
        raise ValueError('Postprocessor altered the visible body')
    return output


def update_sitemaps(site: Path, pages: dict[tuple[str, str], Path]) -> None:
    ns = 'http://www.sitemaps.org/schemas/sitemap/0.9'
    ET.register_namespace('', ns)
    for locale, (prefix, _, _) in LOCALES.items():
        path = site / prefix / 'sitemap.xml'
        tree = ET.parse(path)
        root = tree.getroot()
        for entry in list(root):
            url = entry.find(f'{{{ns}}}loc')
            if url is None or not url.text:
                continue
            expected_prefix = SITE_ROOT + locale_path(locale, '')
            if not url.text.startswith(expected_prefix):
                raise ValueError(f'Unexpected sitemap URL: {url.text}')
            route = url.text[len(expected_prefix):]
            page = pages.get((locale, route))
            if page is None:
                raise ValueError(f'Unresolvable sitemap entry: {url.text}')
            head = HEAD.search(page.read_text(encoding='utf-8')).group(2)
            if re.search(r'<meta\s+name="robots"\s+content="[^"]*noindex', head, re.I):
                root.remove(entry)
                continue
            source = page_source(locale, route)
            date_str = last_mod(source) if source else None
            lastmod = entry.find(f'{{{ns}}}lastmod')
            if date_str:
                if lastmod is None:
                    lastmod = ET.SubElement(entry, f'{{{ns}}}lastmod')
                lastmod.text = date_str
            elif lastmod is not None:
                # A build date is not a content modification date.
                entry.remove(lastmod)
        tree.write(path, encoding='utf-8', xml_declaration=True)


def finalize(site: Path) -> None:
    pages = html_pages(site)
    if len(pages) < 20:
        raise ValueError('Site unexpectedly contains too few HTML pages')
    render_cards(site)
    for (locale, route), path in pages.items():
        old = path.read_text(encoding='utf-8')
        path.write_text(update_head(old, locale=locale, route=route, pages=pages), encoding='utf-8')
    update_sitemaps(site, pages)
    print(f'SEO metadata verified and updated on {len(pages)} content pages across 3 locales.')


if __name__ == '__main__':
    finalize(Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'site')
