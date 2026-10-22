"""Validate multilingual blog metadata, categories, covers and translated slugs."""
from pathlib import Path
from datetime import date,datetime
import re,sys,yaml
ROOT=Path(__file__).resolve().parents[1]
LANGS=('zh-hant','en','zh-hans')
CATEGORIES={'Field Notes','Playbooks','Toolkit'}
SLUG=re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
def meta(path):
    text=path.read_text(encoding='utf-8')
    if not text.startswith('---\n'):raise ValueError(f'{path}: YAML front matter missing')
    try: data=yaml.safe_load(text.split('---\n',2)[1])
    except (ValueError,yaml.YAMLError) as e:raise ValueError(f'{path}: invalid YAML: {e}') from e
    if not isinstance(data,dict):raise ValueError(f'{path}: expected a YAML mapping')
    return data
def check_post(path,locale):
    d=meta(path)
    for key in ('title','date','slug','description','categories','tags','featured_image','status'):
        if key not in d:raise ValueError(f'{path}: missing {key}')
    if not SLUG.fullmatch(str(d['slug'])):raise ValueError(f'{path}: invalid slug')
    if not isinstance(d['date'],(date,datetime,str)):raise ValueError(f'{path}: invalid date')
    if d['status'] not in ('review','published'):raise ValueError(f'{path}: status must be review or published')
    if not isinstance(d['categories'],list) or len(d['categories'])!=1 or d['categories'][0] not in CATEGORIES:
        raise ValueError(f'{path}: categories must be one of {sorted(CATEGORIES)}')
    if not isinstance(d['tags'],list):raise ValueError(f'{path}: tags must be a list')
    if not isinstance(d.get('featured',False),bool):raise ValueError(f'{path}: featured must be boolean')
    order=d.get('featured_order',9999)
    if isinstance(order,bool) or not isinstance(order,int) or order<1:raise ValueError(f'{path}: invalid featured_order')
    image=str(d['featured_image'])
    if not image.startswith('assets/covers/') or '..' in image or not image.endswith(('.png','.jpg','.jpeg','.webp','.svg')):
        raise ValueError(f'{path}: invalid featured_image path')
    if not (ROOT/'shared'/'assets'/'covers'/image.removeprefix('assets/covers/')).is_file():
        raise ValueError(f'{path}: featured_image does not exist: {image}')
    return d
def validate():
    index={l:{p.relative_to(ROOT/'content'/l/'blog'/'posts').as_posix():p for p in (ROOT/'content'/l/'blog'/'posts').rglob('*.md')} for l in LANGS}
    errors=[];metadata={};slugs={}
    for l,entries in index.items():
        slugs[l]=set()
        for name,p in entries.items():
            try:
                d=check_post(p,l)
                if d['slug'] in slugs[l]:raise ValueError(f'{p}: duplicate slug')
                slugs[l].add(d['slug']);metadata[(l,name)]=d
            except ValueError as e:errors.append(str(e))
    for name in index['zh-hant']:
        source=metadata.get(('zh-hant',name))
        for l in ('en','zh-hans'):
            translated=metadata.get((l,name))
            if translated is None:errors.append(f'{name}: missing {l} translation');continue
            if source:
                for key in ('slug','date','categories','featured','featured_order','featured_image','status','draft'):
                    if source.get(key)!=translated.get(key):errors.append(f'{l}/{name}: {key} differs from zh-hant')
    for l in ('en','zh-hans'):
        for name in index[l]:
            if name not in index['zh-hant']:errors.append(f'{l}/{name}: no source article')
    if errors:raise ValueError('Content validation failed:\n'+'\n'.join(' - '+x for x in errors))
    print(f'Validated {len(index["zh-hant"])} posts across three languages.')
if __name__=='__main__':
    try:validate()
    except ValueError as e:print(e,file=sys.stderr);sys.exit(1)
