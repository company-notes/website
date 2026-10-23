"""Derive all magazine home content and topic listings from translated Blog posts."""
from __future__ import annotations
from datetime import date,datetime
from pathlib import Path
import json
from jinja2 import Environment,FileSystemLoader,select_autoescape
from check_content import check_post,validate
ROOT=Path(__file__).resolve().parents[1]
LOCALES=('zh-hant','en','zh-hans')
MESSAGES={
'zh-hant':{'review':'AI 初稿 · 待人工校稿','field':'實戰日誌','playbooks':'方法論','toolkit':'工具箱','empty':'文章整理中','index':'文章由 Blog 分類自動整理；待校稿內容尚未經過人工驗證。'},
'en':{'review':'AI draft · Review pending','field':'Field notes','playbooks':'Playbooks','toolkit':'Toolkit','empty':'More articles coming','index':'Articles are grouped automatically from Blog categories. Drafts marked for review have not been verified.'},
'zh-hans':{'review':'AI 初稿 · 待人工审核','field':'实战日志','playbooks':'方法论','toolkit':'工具箱','empty':'文章整理中','index':'文章根据 Blog 分类自动整理；待审核内容尚未经人工验证。'}
}
def read_posts(locale):
    posts=[]
    for path in (ROOT/'content'/locale/'blog'/'posts').rglob('*.md'):
        d=check_post(path,locale)
        if d.get('draft') is True:continue
        val=d['date'];day=val.isoformat() if isinstance(val,(date,datetime)) else str(val)
        category=d['categories'][0];review=d['status']=='review'
        category_label={'Field Notes':MESSAGES[locale]['field'],'Playbooks':MESSAGES[locale]['playbooks'],'Toolkit':MESSAGES[locale]['toolkit']}[category]
        posts.append(dict(title=str(d['title']),date_iso=day,date_display=day.replace('-','.'),
            href='blog/'+d['slug']+'/',image=d['featured_image'],
            image_alt=d.get('featured_image_alt',d['title']),
            excerpt=str(d['description']).strip(),category=category,category_label=category_label,
            featured=d.get('featured',False),featured_order=d.get('featured_order',9999),review=review,slug=d['slug']))
    posts.sort(key=lambda p:(p['date_iso'],p['slug']),reverse=True)
    return posts
def featured_posts(posts):
    return sorted((p for p in posts if p['featured']),key=lambda p:(p['featured_order'],-int(p['date_iso'].replace('-','')),p['slug']))
def render_category_pages(locale,posts):
    msg=MESSAGES[locale];root=ROOT/'content'/locale
    for category,dest,key in [('Playbooks','playbooks/index.md','playbooks'),('Toolkit','toolkit/index.md','toolkit')]:
        entries=[p for p in posts if p['category']==category]
        lines=['---',f'title: {msg[key]}','---','',f'# {msg[key]}','',msg['index'],'']
        if category=='Toolkit':
            from html import escape
            resources=json.loads((ROOT/'templates'/'toolkit_resources.json').read_text(encoding='utf-8'))[locale]
            columns=resources['columns']
            lines += [f'## {resources["heading"]}', '',
                      '<div class="cn-toolkit-table-wrap" role="region" aria-label="'+escape(resources['heading'],quote=True)+'">',
                      '<table class="cn-toolkit-table">',
                      '<thead><tr>'+''.join(f'<th scope="col">{escape(label)}</th>' for label in columns)+'</tr></thead>',
                      '<tbody>']
            for item in resources['resources']:
                image=f'../{item["image"]}'
                links='<br>'.join(
                    f'<a href="{escape(link["url"],quote=True)}" rel="noopener noreferrer">{escape(link["label"])} ↗</a>'
                    for link in item['links'])
                lines += [
                    '<tr>',
                    f'<th scope="row" class="cn-toolkit-tool"><img src="{escape(image,quote=True)}" alt="{escape(item["image_alt"],quote=True)}" width="192" height="120" loading="lazy"><strong>{escape(item["name"])}</strong></th>',
                    f'<td class="cn-toolkit-description">{escape(item["description"])}</td>',
                    f'<td class="cn-toolkit-links">{links}</td>',
                    '</tr>',
                ]
            lines += ['</tbody></table></div>', '', f'## {resources["articles_heading"]}', '']
        if entries:
            for p in entries:
                badge=f' — **{msg["review"]}**' if p['review'] else ''
                level='###' if category=='Toolkit' else '##'
                lines += [f'{level} [{p["title"]}](../blog/{p["slug"]}/)','',p['excerpt']+badge,'']
        else:lines += [msg['empty'],'']
        (root/dest).write_text('\n'.join(lines).rstrip()+'\n',encoding='utf-8')
def render_homepages():
    validate()
    env=Environment(loader=FileSystemLoader(str(ROOT/'templates')),autoescape=select_autoescape(default=True))
    template=env.get_template('home.html.j2')
    copy=json.loads((ROOT/'templates/homepages.json').read_text(encoding='utf-8'))
    for locale in LOCALES:
        posts=read_posts(locale);feat=featured_posts(posts);lead=feat[0] if feat else (posts[0] if posts else None)
        rail=[p for p in feat if lead and p['slug']!=lead['slug']][:2]
        if len(rail)<2:rail += [p for p in posts if (not lead or p['slug']!=lead['slug']) and p not in rail][:2-len(rail)]
        playbooks=[p for p in feat if p['category']=='Playbooks']
        playbooks += [p for p in posts if p['category']=='Playbooks' and p not in playbooks]
        toolkit=[p for p in feat if p['category']=='Toolkit']
        toolkit += [p for p in posts if p['category']=='Toolkit' and p not in toolkit]
        guides=playbooks[:2]+toolkit[:1]
        carousel=[dict(kind=p['category_label'],title=p['title'],excerpt=p['excerpt'],href=p['href'],review=p['review']) for p in feat[:5]]
        params={**copy[locale],'review_label':MESSAGES[locale]['review'],'no_articles':MESSAGES[locale]['empty']}
        content=template.render(**params,featured=lead,rail=rail,guides=guides,posts=posts[:6],carousel_items=carousel)
        (ROOT/'content'/locale/'index.md').write_text(content.rstrip()+'\n',encoding='utf-8')
        render_category_pages(locale,posts)
        print(f'{locale}: {len(posts)} published/review posts, {len(feat)} featured')
if __name__=='__main__':render_homepages()
