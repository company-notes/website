"""Render magazine front pages from translated Markdown post frontmatter.

The blog itself remains fully managed by the MkDocs Material blog plugin.
New posts automatically appear on the homepage on the next build.
"""
from __future__ import annotations
from datetime import date, datetime
from html import escape
from pathlib import Path
import json
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parents[1]
LOCALES = ('zh-hant', 'en', 'zh-hans')

def translated_posts(locale: str):
    from check_content import meta
    posts=[]
    for path in (ROOT / 'content' / locale / 'blog' / 'posts').rglob('*.md'):
        data=meta(path)
        if data.get('draft') is True:
            continue
        day=data['date']
        iso=day.isoformat() if isinstance(day,(date,datetime)) else str(day)
        slug=str(data['slug'])
        image=str(data.get('cover', 'assets/covers/field-notes.svg'))
        # Only local repository-controlled cover assets are used in generated markup.
        if not image.startswith('assets/covers/') or '..' in image or '"' in image or "'" in image:
            raise ValueError(f'Invalid cover path: {path} {image}')
        description=str(data.get('description', '')).strip()
        posts.append({
            'title': str(data['title']),
            'date_iso': iso,
            'date_display': iso.replace('-', '.'),
            'href': 'blog/'+slug+'/',
            'image': image,
            'image_alt': str(data.get('cover_alt', 'Company Notes editorial illustration')),
            'excerpt': description or str(data['title']),
        })
    posts.sort(key=lambda p:(p['date_iso'],p['href']),reverse=True)
    return posts

def render_homepages():
    env=Environment(loader=FileSystemLoader(str(ROOT / 'templates')),autoescape=select_autoescape(enabled_extensions=('j2',), default=True))
    tpl=env.get_template('home.html.j2')
    copy=json.loads((ROOT/'templates/homepages.json').read_text(encoding='utf-8'))
    for locale in LOCALES:
        posts=translated_posts(locale)
        if not posts:
            raise ValueError(f'No published blog posts in {locale}; add at least one before publishing.')
        info=copy[locale]
        carousel_items=[dict(kind=info['carousel_post_label'],title=p['title'],excerpt=p['excerpt'],href=p['href']) for p in posts[:3]]
        carousel_items += [
            dict(kind=info['label_playbook'],title=info['organization_title'],excerpt=info['organization_desc'],href='playbooks/organization/'),
            dict(kind=info['label_playbook'],title=info['operations_title'],excerpt=info['operations_desc'],href='playbooks/daily-operations/'),
        ]
        page=tpl.render(**info,featured=posts[0],posts=posts[:6],carousel_items=carousel_items)
        (ROOT/'content'/locale/'index.md').write_text(page.rstrip()+'\n',encoding='utf-8')
        print(f'Rendered {locale} magazine homepage with {len(posts[:6])} article(s)')

if __name__=='__main__':
    render_homepages()
