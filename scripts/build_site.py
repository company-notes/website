#!/usr/bin/env python3
"""Build Company Notes' three independently localized Material blogs.

No mkdocs-static-i18n dependency: the built-in Material blog has had
compatibility issues with it. Markdown paths/slugs are identical across locales.
"""
from __future__ import annotations
import argparse
import copy
from pathlib import Path
import shutil
import subprocess
import sys
import yaml
from render_home import render_homepages
from seo_postprocess import finalize

ROOT = Path(__file__).resolve().parents[1]
LOCALES = {
    'zh-hant': {'prefix': '', 'theme': 'zh-Hant', 'description': '一個人與 AI 團隊的真實公司營運實驗、架構和工具。', 'nav': ['首頁','文章','方法論','工具箱','關於']},
    'en': {'prefix': 'en', 'theme': 'en', 'description': 'Field notes on running a real company with AI agents, systems and workflows.', 'nav': ['Home','Writing','Playbooks','Toolkit','About']},
    'zh-hans': {'prefix': 'zh-hans', 'theme': 'zh', 'description': '一个人与 AI 团队的真实公司运营实验、架构和工具。', 'nav': ['首页','文章','方法论','工具箱','关于']},
}
NAV_PATHS = ['index.md','blog/index.md','playbooks/index.md','toolkit/index.md','about.md']


def prepare_assets():
    src = ROOT / 'shared'
    for locale in LOCALES:
        for subdir in ('stylesheets', 'javascripts', 'assets'):
            dest = ROOT / 'content' / locale / subdir
            dest.mkdir(parents=True, exist_ok=True)
            for path in (src / subdir).rglob('*'):
                if path.is_file():
                    target = dest / path.relative_to(src / subdir)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(path, target)


def build():
    from check_content import validate
    validate()
    render_homepages()
    prepare_assets()
    base = yaml.safe_load((ROOT / 'mkdocs.yml').read_text(encoding='utf-8'))
    site_dir = ROOT / 'site'
    if site_dir.exists():
        shutil.rmtree(site_dir)
    site_dir.mkdir()
    for locale, language in LOCALES.items():
        config = copy.deepcopy(base)
        config['site_url'] = 'https://company-notes.com/' + (language['prefix'] + '/' if language['prefix'] else '')
        config['site_description'] = language['description']
        config['docs_dir'] = f'content/{locale}'
        config['site_dir'] = 'site/' + language['prefix'] if language['prefix'] else 'site'
        config['edit_uri'] = f'edit/main/content/{locale}/'
        config['theme']['language'] = language['theme']
        config['extra']['locale'] = locale
        config['nav'] = [{label: path} for label, path in zip(language['nav'], NAV_PATHS)]
        config_path = ROOT / f'.mkdocs.{locale}.generated.yml'
        config_path.write_text(yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding='utf-8')
        print(f'Building {locale} -> {config["site_dir"]}', flush=True)
        try:
            subprocess.run([sys.executable, '-m', 'mkdocs', 'build', '--config-file', str(config_path), '--clean'], cwd=ROOT, check=True)
        finally:
            config_path.unlink(missing_ok=True)
    # Rewrite metadata only; all visible page bodies remain byte-for-byte intact.
    finalize(site_dir)
    # GitHub Pages recognizes the custom domain after it is also configured in Settings > Pages.
    (site_dir / 'CNAME').write_text('company-notes.com\n', encoding='utf-8')
    (site_dir / '.nojekyll').write_text('', encoding='utf-8')
    (site_dir / 'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: https://company-notes.com/sitemap.xml\nSitemap: https://company-notes.com/en/sitemap.xml\nSitemap: https://company-notes.com/zh-hans/sitemap.xml\n', encoding='utf-8')
    print('Done: site/ (zh-Hant /, English /en/, Simplified /zh-hans/)')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--prepare-only', action='store_true', help='Copy shared assets for mkdocs serve')
    parser.add_argument('--validate-only', action='store_true', help='Check all three source trees without building')
    args = parser.parse_args()
    if args.validate_only:
        from check_content import validate
        validate()
        for locale in LOCALES:
            for path in NAV_PATHS:
                assert (ROOT / 'content' / locale / path).is_file(), f'Missing {locale}/{path}'
        print('All 3 locale trees passed basic checks.')
    elif args.prepare_only:
        render_homepages()
        prepare_assets()
        print('Assets prepared. Run: python -m mkdocs serve')
    else:
        build()
