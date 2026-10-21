"""Ensure released articles have matching EN, Traditional Chinese, and Simplified Chinese files."""
from pathlib import Path
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]
LANGS = ('zh-hant', 'en', 'zh-hans')

def meta(path):
    text = path.read_text(encoding='utf-8')
    if not text.startswith('---\n'):
        raise ValueError(f'{path}: blog post must start with YAML front matter')
    try:
        data = text.split('---\n', 2)[1]
        result = yaml.safe_load(data) or {}
    except Exception as err:
        raise ValueError(f'{path}: invalid front matter: {err}') from err
    for required in ('title', 'date', 'slug'):
        if required not in result:
            raise ValueError(f'{path}: missing {required}')
    return result

def validate():
    folders = {lang: ROOT / 'content' / lang / 'blog' / 'posts' for lang in LANGS}
    paths = {lang: {p.name:p for p in folder.rglob('*.md')} for lang,folder in folders.items()}
    errors=[]
    for name,zh_path in paths['zh-hant'].items():
        try:
            zh = meta(zh_path)
        except ValueError as err:
            errors.append(str(err));continue
        if zh.get('draft') is True:
            continue
        for lang in ('en','zh-hans'):
            other = paths[lang].get(name)
            if other is None:
                errors.append(f'Missing {lang} translation for published post: {name}')
                continue
            try:
                data = meta(other)
                if str(data['date']) != str(zh['date']) or data['slug'] != zh['slug']:
                    errors.append(f'{lang}/{name}: date and slug must match zh-hant')
            except ValueError as err:
                errors.append(str(err))
    for lang in ('en','zh-hans'):
        for name in paths[lang]:
            if name not in paths['zh-hant']:
                errors.append(f'{lang}/{name}: no zh-hant source post')
    if errors:
        raise ValueError('Content checks failed:\n' + '\n'.join(' - '+x for x in errors))
    print(f'Content checked: {len(paths["zh-hant"])} source posts; published posts have translations.')

if __name__ == '__main__':
    try:
        validate()
    except ValueError as err:
        print(err, file=sys.stderr)
        sys.exit(1)
