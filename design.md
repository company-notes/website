# Company Notes — Design System

Version: Editorial Magazine / October 2026. This supersedes the earlier text-only newspaper layout.

## Intent

Company Notes is **a real working journal about running a company alongside AI agents**, not an AI headlines aggregator, a consulting agency landing page, or an imitation of a software dashboard. The user supplied Help Scout Blog and Pando Blog as editorial references: borrow their *information hierarchy, illustrated article covers, magazine pacing, and distinct sections*, not their images, branding, or exact CSS.

## Genre / page structure

- Genre: editorial; warm, contemporary tech publication.
- Homepage macrostructure: **Ecosystem Index / illustrated magazine** (one dominant recent article, two adjacent reading suggestions, topic pathways, dynamically generated recent-article grid, editorial note, colophon).
- Article pages: long-form readable content with strong typography and generous width controls, preserving Material Blog functionality and per-language URLs.
- Overall navigation: retain Material header, search and native language chooser; home adds local anchor topic rail.
- No fake articles, fabricated metrics, newsletter forms without a backend, testimonials, simulated IDE panels, or generic gradients.

## Theme

The canonical variables live in `shared/stylesheets/tokens.css`. Tint the paper warm and text ink slightly blue; reserve vivid blue for links and navigation; SVG illustrations may have their own deliberate palette.

- `--color-paper`: `oklch(98.4% .006 80)`
- `--color-paper-2`: `oklch(95.9% .009 77)`
- `--color-ink`: `oklch(21% .022 263)`
- `--color-ink-2`: `oklch(40% .016 263)`
- `--color-rule`: `oklch(86% .011 263)`
- `--color-accent`: `oklch(51% .20 261)`
- `--color-focus`: `oklch(58% .18 261)`

## Typography

- Display: **Space Grotesk** (roman, 700), plus `Noto Sans TC / SC` system fallbacks for Chinese.
- Body: **Manrope** 400–800 plus the same CJK fallbacks.
- Mono: system mono, reserved for actual code.
- Long-form article measure: about 74ch; no italic headlines, no all-uppercase section eyebrows repeated everywhere.

## Layout and spacing

- Main homepage max-width: 80rem.
- Magazine cover aspect: 1200:720; small sidebar covers can be cropped into horizontal strips.
- Primary grid: 1.68fr / .86fr (lead + two supporting pieces), collapses to one column on tablets.
- Topic feature grid: 3 columns on wide screens, 2 tablet, 1 mobile.
- Design tokens use named 4pt increments. Interactive labels stay one line.

## Motion and accessibility

- Motion limited to a 1.025× cover-image hover zoom (hover-capable pointers only); no ornamental scroll animations.
- Focus-visible outlines, accessible SVG description, lazy loading except priority cover, `prefers-reduced-motion` respected.
- `html,body { overflow-x: clip }`; test layouts at 320, 375, 414, 768 and desktop widths.

## Editorial workflow

1. Write one article per language in `content/<locale>/blog/posts/` using the same filename/date/slug.
2. Optional frontmatter: `description:`, `cover: assets/covers/filename.svg`, `cover_alt:`.
3. `scripts/render_home.py` reads post frontmatter and generates homepage teaser cards automatically for all three locales.
4. `scripts/build_site.py` validates 3-language parity, renders homepage, copies art and assets, and runs MkDocs Material separately for each locale.
5. New cover art goes in `shared/assets/covers/` and should illustrate the article's real subject rather than invent product screenshots.

## What must remain consistent

Company Notes identity, color tokens, cover language, navigation, reading measures, and typography across homepage, Blog, Playbooks, Toolkit, About and all three languages. Homepage module ordering can evolve without altering route names or article slugs.

## Provenance

Design direction was informed by user-supplied screenshots of `https://www.helpscout.com/blog/` and `https://pando.com/blog`. The page is an original composition, not a pixel copy; no source images were reused.
