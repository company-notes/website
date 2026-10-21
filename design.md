# Design — Company Notes

This is the shared Hallmark design system for the Company Notes editorial website, including the homepage, Markdown blog, playbooks and toolkit. Preserve existing locale routes and MkDocs Material functionality.

## Genre and voice

- Genre: **Editorial**. Tone: a working technical journal, specific and unembellished, not an AI/SaaS marketing landing page.
- Primary audience: technically curious solo founders and small-business owners designing actual AI-operated workflows.
- Primary action: **read a real field note**. Secondary: find a method, template or MCP integration.
- No fabricated claims, metrics, testimonials, release announcements, or feature availability.

## Page structure

- Homepage: **Index-First**, an editorial masthead leading into a browsable annotated link index (Hallmark N6 Newspaper Masthead and Ft4 Dense Typographic colophon). No three-card feature grid, no giant abstract visual.
- Blog and individual articles: long-document editorial typography, readable measure, hairline rules, minimal navigation.
- Playbooks / toolkit / about: straightforward documents and lists. Same brand tokens, a different content rhythm from the homepage.

## Theme: Newsprint, warm paper with a single vermilion accent

All full tokens are in `shared/stylesheets/tokens.css` and auto-copied to each locale on build.

- `--color-paper`: `oklch(97% 0.009 84)`
- `--color-paper-2`: `oklch(94% 0.013 84)`
- `--color-ink`: `oklch(22% 0.019 76)`
- `--color-ink-2`: `oklch(36% 0.013 76)`
- `--color-rule`: `oklch(79% 0.018 80)`
- `--color-accent`: `oklch(48% 0.132 33)`
- `--color-focus`: `oklch(52% 0.16 33)`

Accent should remain on links, editorial accents and keyboard focus rather than large colour fills.

## Typography

- Display: **Fraunces** and East Asian serif fallback, roman only, with geometric tracking.
- Body: **Manrope** and native East Asian sans fallbacks; readable line length (~65–72ch).
- Optional technical code font: monospace, only in code blocks.
- UI typography does not default to Roboto/Inter. Headings are never italic.

## Spacing / motion / interaction

- Named 4pt-based tokens (`--space-*`) in tokens.css, not one-off section padding.
- Rule-based editorial separation, no repeated boxed cards.
- Transition only when it communicates focus / navigation; colour/background transitions under 200 ms.
- `prefers-reduced-motion: reduce` disables movement; visible focus rings and mobile menu are mandatory.
- Viewports 320 / 375 / 414 / 768 / desktop must not overflow horizontally; responsive columns stack below content-driven breakpoints.

## Shared across all pages

- The wordmark, paper and ink palette, serif display/sans body pairing, subtle rules, and honest editorial copy.
- The homepage is the only page with a large masthead; reading pages keep Material's practical navigation and search.
- Existing three-locale Markdown and GitHub Pages deployment are part of the implementation contract; never replace them with a JS-only SPA.

## Exports

`shared/stylesheets/tokens.css` is the authoritative CSS export. It is automatically copied to `/stylesheets/tokens.css`, `/en/stylesheets/tokens.css`, and `/zh-hans/stylesheets/tokens.css` by `scripts/build_site.py`.
