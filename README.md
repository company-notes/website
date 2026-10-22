# Company Notes — Website

The three-language Company Notes publication at https://company-notes.com/, powered by MkDocs Material Blog, Markdown, Python scripts, and GitHub Pages.

## How to publish a real Blog article

Create the same filename under all three language folders: content/zh-hant/blog/posts/, content/en/blog/posts/, and content/zh-hans/blog/posts/. Translate the title, description, alt text and body; keep the slug and other classification fields consistent.

Example frontmatter for a Traditional Chinese article:

    ---
    title: 我如何讓 Grok Bot 操作 ERPNext
    date: 2026-11-01
    slug: grokbot-erpnext
    description: MCP 系統整合與授權架構的實際紀錄。
    categories: [Toolkit]
    tags: [MCP, ERPNext, permissions]
    featured_image: assets/covers/integrations.svg
    featured_image_alt: 系統串接示意圖
    featured: true
    featured_order: 5
    status: review
    ---

Write a Markdown title, introductory paragraph, an HTML comment reading more between the two dashes, and your article content. The built-in Blog plugin handles category archives, tags, post URLs and pagination.

## Classification rules (frontmatter is the only source of truth)

- Field Notes, Playbooks, Toolkit are the three allowed categories. Set exactly one in the categories list.
- Playbooks articles appear on the automatically generated Playbooks index and up to two guide tiles on the homepage.
- Toolkit articles appear on the Toolkit index and one guide tile on the homepage.
- All articles appear in the newest-posts area, sorted by date.
- featured: true makes the post eligible for the featured lead, two supporting stories, and the reading carousel.
- featured_order: 1 gives higher priority than 2 or 3. It is optional; when omitted, the post sorts behind ranked featured items.
- featured_image is required for publicly displayed articles. Store the asset in shared/assets/covers/ (SVG, PNG, WebP, JPEG).
- tags offer finer discovery within the MkDocs Blog.

## Editorial stages and credibility

- status: review — a PUBLICLY visible article which is clearly labelled AI-generated draft awaiting human review both on the homepage and article. The post has a noindex directive. This is not a private draft.
- status: published — an article verified, revised and proofread by a human; the warning and noindex disappear.
- draft: true — an unpublished post, excluded by MkDocs Material and the homepage compiler from the production site. This is suitable for work that is not ready to display at all.

The four starter articles are all status: review. These are AI-written outlines, not audited operational case studies. The first editorial task is to replace illustrative generalities with actual hands-on evidence before setting status: published.

The site's About page explains that human practical experience and judgment underpin published writing, while AI may help organize, polish and translate. Not 100% AI-free, not raw AI text masquerading as first-hand reporting.

## Updating the homepage

Do not edit content/{locale}/index.md, playbooks/index.md or toolkit/index.md by hand. They are regenerated on every build using scripts/render_home.py, templates/home.html.j2, and templates/homepages.json. The homepage carousel and all article links also come from real Markdown post metadata. The original illustration assets remain in shared/assets/covers/.

Old links to /playbooks/organization/ and /playbooks/daily-operations/ are retained as navigation pages pointing to the actual Blog posts.

## Test and deploy

Install dependencies with pip install -r requirements.txt, then run:

    python -m unittest discover -s tests -v
    python scripts/build_site.py

Push to main: GitHub Actions validates three locales and automatically deploys to GitHub Pages, using the configured company-notes.com custom domain. Traditional Chinese is at /, English at /en/, and Simplified Chinese at /zh-hans/. Translation files are authored separately rather than automatically machine-translated during site building.

Background color and locale selectors continue to work on the published website.

## Language routing for direct article links

- Traditional Chinese lives at `/`, English at `/en/`, and Simplified Chinese at `/zh-hans/`.
- A visitor entering the unprefixed homepage **or a direct article URL** (for example `/blog/grok-bot-backup/`) is routed to the same path under their saved language preference, or the browser language when no preference is saved. Queries and anchors are preserved.
- Explicit `/en/` and `/zh-hans/` links always take precedence over automatic detection. Using the language menu saves the manual choice in local storage; visiting an unprefixed URL can therefore honor it later.
- GitHub Pages serves static HTML, so the automatic redirect is client-side JavaScript. Search engines without JavaScript still see the canonical Traditional Chinese document and the site's alternate-language URLs.
- Run `node tests/test_locale_redirect.cjs` to validate deep links and preferences locally.
