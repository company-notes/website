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
    def test_four_blog_articles_are_homepage_sources(self):
        check_content.validate();render_home.render_homepages()
        items=render_home.read_posts('zh-hant')
        self.assertEqual(len(items),4)
        self.assertEqual([x['slug'] for x in render_home.featured_posts(items)],['why-company-notes','ai-organization','daily-operations','enterprise-mcp'])
        page=(self.root/'content/zh-hant/index.md').read_text()
        for s in ('blog/why-company-notes/','blog/ai-organization/','blog/daily-operations/','blog/enterprise-mcp/'):self.assertIn(s,page)
        self.assertIn('AI 初稿',page)
        self.assertNotIn('href="playbooks/organization/"',page)
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
            self.assertEqual(render_home.featured_posts(render_home.read_posts('en'))[0]['slug'],'new-tool')
            for path in paths:path.write_text(path.read_text().replace('status: published','status: published\ndraft: true'))
            render_home.render_homepages()
            self.assertNotIn('blog/new-tool/',(self.root/'content/en/index.md').read_text())
        finally:
            for path in paths:path.unlink(missing_ok=True)
if __name__=='__main__':unittest.main()
