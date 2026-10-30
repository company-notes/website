"""Editorial publishing regression checks: category placement, featured order and drafts."""
import sys,unittest,tempfile,shutil
from pathlib import Path
import yaml
SOURCE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(SOURCE/'scripts'))
import check_content,render_home
class EditorialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workspace=tempfile.TemporaryDirectory(prefix='company-notes-tests-')
        cls.root=Path(cls.workspace.name)
        for item in ('content','shared','templates'):shutil.copytree(SOURCE/item,cls.root/item)
        cls.old_a=check_content.ROOT;cls.old_b=render_home.ROOT
        check_content.ROOT=cls.root;render_home.ROOT=cls.root
    @classmethod
    def tearDownClass(cls):
        check_content.ROOT=cls.old_a;render_home.ROOT=cls.old_b;cls.workspace.cleanup()
    def test_homepage_uses_current_blog_metadata(self):
        # Never fix the article count or featured slugs: new posts should not break CI.
        check_content.validate()
        render_home.render_homepages()
        items = render_home.read_posts('zh-hant')
        source_posts = (self.root / 'content/zh-hant/blog/posts').rglob('*.md')
        expected_count = sum(not check_content.meta(p).get('draft', False) for p in source_posts)
        self.assertEqual(len(items), expected_count)

        page = (self.root / 'content/zh-hant/index.md').read_text()
        for post in items[:6]:  # the homepage recent-writing module displays six
            self.assertIn(f"blog/{post['slug']}/", page)

        featured = render_home.featured_posts(items)
        if featured:
            self.assertIn(f"blog/{featured[0]['slug']}/", page)

        # Category indexes must include every visible article in their category.
        for category, route in [('Playbooks', 'playbooks'), ('Toolkit', 'toolkit')]:
            category_page = (self.root / f'content/zh-hant/{route}/index.md').read_text()
            for post in items:
                if post['category'] == category:
                    self.assertIn(f"../blog/{post['slug']}/", category_page)

    def test_toolkit_includes_import_bot_and_github_in_all_languages(self):
        render_home.render_homepages()
        resources = __import__('json').loads(
            (self.root / 'templates/toolkit_resources.json').read_text(encoding='utf-8'))
        bot_url = 'https://x.ai/bot/LvdHazZLidr0S3JJAdr8e'
        github_url = 'https://github.com/company-notes/grok-bot-backup'
        self.assertEqual(set(resources), set(render_home.LOCALES))
        for locale in render_home.LOCALES:
            with self.subTest(locale=locale):
                page = (self.root / 'content' / locale / 'toolkit/index.md').read_text()
                self.assertIn(bot_url, page)
                self.assertIn(github_url, page)
                self.assertIn('../blog/enterprise-mcp/', page)
                self.assertIn(resources[locale]['heading'], page)
                self.assertIn(resources[locale]['resources'][0]['name'], page)
                self.assertIn('<div class="cn-toolkit-table-wrap" role="region" tabindex="0"', page)
                self.assertIn('<table class="cn-toolkit-table">', page)
                self.assertIn('<colgroup><col class="cn-toolkit-col-tool"><col class="cn-toolkit-col-description"><col class="cn-toolkit-col-links"></colgroup>', page)
                self.assertIn('<th scope="col">', page)
                self.assertIn('<th scope="row" class="cn-toolkit-tool"><div class="cn-toolkit-identity">', page)
                self.assertIn('class="cn-toolkit-link-list"', page)
                self.assertIn('class="cn-toolkit-action cn-toolkit-action-primary"', page)
                self.assertEqual(page.count('class="cn-toolkit-action'), 2)
                self.assertNotIn('<br>', page)
                self.assertIn('src="../assets/toolkit/grok-bot-backup.svg"', page)
                self.assertIn('alt="'+resources[locale]['resources'][0]['image_alt']+'"', page)
                self.assertIn('width="192" height="120"', page)
                self.assertEqual([link['url'] for link in resources[locale]['resources'][0]['links']],
                                 [bot_url, github_url])
        import xml.etree.ElementTree as ET
        source_svg=self.root/'shared/assets/toolkit/grok-bot-backup.svg'
        self.assertTrue(source_svg.is_file())
        svg_root=ET.parse(source_svg).getroot()
        self.assertEqual(svg_root.attrib['viewBox'], '0 0 900 560')
        self.assertEqual(svg_root.attrib['role'], 'img')

        css=(self.root/'shared/stylesheets/site.css').read_text(encoding='utf-8')
        self.assertIn('min-width: 800px;', css)
        self.assertIn('table-layout: fixed;', css)
        self.assertIn('border: 1.5px solid var(--color-rule);', css)
        self.assertIn('.cn-toolkit-col-links { width: 27%; }', css)
        self.assertIn('a.cn-toolkit-action-primary', css)

    def test_openwhispr_article_is_published_in_all_languages_with_sanitized_images(self):
        slug = 'openwhispr-groq-cloudflare-typeless'
        images = ['01-groq-whisper.webp', '02-cloudflare-cleanup.webp',
                  '03-prompt-studio.webp']
        for name in images:
            asset = self.root / 'shared/assets/posts/openwhispr-typeless' / name
            self.assertTrue(asset.is_file(), str(asset))
            self.assertEqual(asset.read_bytes()[:4], b'RIFF')
            self.assertEqual(asset.read_bytes()[8:12], b'WEBP')
        for locale in render_home.LOCALES:
            with self.subTest(locale=locale):
                article = self.root / 'content' / locale / 'blog/posts' / f'2026-10-29-{slug}.md'
                body = article.read_text(encoding='utf-8')
                self.assertIn('status: published', body)
                self.assertIn('https://github.com/company-notes/dictation-cleaner', body)
                self.assertIn('"version": "2.8.0"', body)
                self.assertEqual(body.count('<!-- more -->'), 1)
                self.assertNotIn('佔位', body)
                self.assertNotIn('發文前編輯備忘', body)
                for image in images:
                    self.assertIn(f'../../assets/posts/openwhispr-typeless/{image}', body)

    def test_openwhispr_result_video_is_embedded_after_the_cost_paragraph(self):
        from pathlib import Path
        root = self.root / 'shared/assets/posts/openwhispr-typeless'
        video = root / 'My_Typeless.mp4'
        poster = root / 'My_Typeless_poster.jpg'
        self.assertTrue(video.is_file())
        self.assertEqual(video.read_bytes()[4:8], b'ftyp')
        self.assertGreater(video.stat().st_size, 100000)
        self.assertTrue(poster.is_file())
        self.assertEqual(poster.read_bytes()[:2], bytes([0xff, 0xd8]))
        anchors = {
            'zh-hant': ('因此我就在研究有沒有簡單又便宜的方法。', '最後的成果'),
            'en': ('So I started looking for something simpler and cheaper.', 'The final result'),
            'zh-hans': ('所以我就开始琢磨，有没有简单又便宜的办法。', '最终成果'),
        }
        for locale, (intro_end, caption) in anchors.items():
            with self.subTest(locale=locale):
                path = self.root / 'content' / locale / 'blog/posts/2026-10-29-openwhispr-groq-cloudflare-typeless.md'
                body = path.read_text(encoding='utf-8')
                video_path = '../../assets/posts/openwhispr-typeless/My_Typeless.mp4'
                poster_path = '../../assets/posts/openwhispr-typeless/My_Typeless_poster.jpg'
                self.assertEqual(body.count('class="cn-post-video"'), 1)
                self.assertIn('max-width:520px;margin:1.25rem auto 1.65rem;text-align:center', body)
                self.assertIn('width="520" height="444"', body)
                self.assertIn('style="display:block;width:100%;max-width:520px;height:auto;margin:0 auto;"', body)
                self.assertIn(f'poster="{poster_path}"', body)
                self.assertIn(f'<source src="{video_path}" type="video/mp4">', body)
                self.assertIn(f'<figcaption>{caption}</figcaption>', body)
                self.assertLess(body.index(intro_end), body.index('<figure class="cn-post-video">'))
                self.assertLess(body.index('</figure>'), body.index('<!-- more -->'))
                self.assertIn('controls playsinline preload="metadata"', body)
        css=(self.root / 'shared/stylesheets/site.css').read_text(encoding='utf-8')
        self.assertIn('max-width: 520px;', css)
        self.assertIn('margin: 1.25rem auto 1.65rem;', css)

    def test_new_post_feature_and_draft_exclusion(self):
        paths=[]
        try:
            for lang in render_home.LOCALES:
                path=self.root/'content'/lang/'blog/posts/2026-10-23-new-tool.md'
                metadata={'title':'Test article','date':'2026-10-23','slug':'new-tool','description':'Test metadata-driven homepage.',
                   'categories':['Toolkit'],'tags':['MCP'],'featured':True,'featured_order':1,
                   'featured_image':'assets/covers/integrations.svg','status':'published'}
                path.write_text('---\n'+yaml.safe_dump(metadata)+'---\n\n# Test article\n\nBody.\n')
                paths.append(path)
            render_home.render_homepages()
            featured_slugs = [p['slug'] for p in render_home.featured_posts(render_home.read_posts('en'))]
            self.assertIn('new-tool', featured_slugs)
            self.assertIn('../blog/new-tool/', (self.root/'content/en/toolkit/index.md').read_text())
            for path in paths:path.write_text(path.read_text().replace('status: published','status: published\ndraft: true'))
            render_home.render_homepages()
            self.assertNotIn('blog/new-tool/',(self.root/'content/en/index.md').read_text())
        finally:
            for path in paths:path.unlink(missing_ok=True)
if __name__=='__main__':unittest.main()
