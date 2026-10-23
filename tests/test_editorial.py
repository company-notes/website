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
                self.assertEqual([link['url'] for link in resources[locale]['resources'][0]['links']],
                                 [bot_url, github_url])

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
