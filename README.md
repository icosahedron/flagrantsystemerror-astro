# Flagrant System Error

The blog at [flagrantsystemerror.com](https://flagrantsystemerror.com), built with
[Astro](https://astro.build) as a fully static site. Content lives as Markdown in
this repo, styled to look like Notion. There is no server and no dependency on
Notion at build or run time.

## Quick start

```bash
npm install
npm run dev        # live preview at http://localhost:4321
npm run build      # type-checks, then writes the static site to dist/
npm run preview    # serve the built dist/ locally to sanity-check
```

## Publishing a new post

**Drop a Markdown file into `src/content/blog/` and it publishes itself.** On the
next build it automatically:

- appears on the home page archive (newest first, by `pubDate`),
- gets its own page at `/<filename>/` — the filename is the URL slug,
- is added to the RSS feed (`/rss.xml`) and `sitemap.xml`.

Nothing else to wire up. There is no draft flag: every file in `src/content/blog/`
is published on the next build. To stage a post, keep it outside that folder until
it's ready.

### Frontmatter

```markdown
---
title: "My Post Title"        # required
pubDate: 2026-07-24           # required — controls archive/feed ordering
description: "One line shown in the archive, RSS, and page metadata."
updatedDate: 2026-07-25       # optional
heroImage: "/images/covers/my-cover.jpg"   # optional cover banner
heroImagePosition: 0.5        # optional, 0=top .. 1=bottom focal point
icon: "📘"                    # optional emoji, shown on the cover and in the archive
---

Body starts here.
```

Only `title` and `pubDate` are required. Put a cover image in `public/` (e.g.
`public/images/covers/`) and point `heroImage` at it with a site-absolute path.

### Notion-style content

Beyond normal Markdown, the build understands:

- **Callouts** — `:::callout{icon="💡"}` … `:::`
- **Figures** (centered image + caption) — `:::figure{src="/images/…png"}` caption `:::`
- **Bookmarks / embeds** — `:::bookmark{url="…"}` title `:::` and `:::embed{url="…"}` … `:::`
- **Math** — `$inline$` and `$$block$$` render with KaTeX; an equation alone on a
  line is centered as display math.

## Standalone pages

Pages that are not blog posts (About, Colophon) live in `src/content/pages/` and
each has a small route file in `src/pages/` (e.g. `about.astro`). To add another,
copy `src/pages/about.astro`, create the matching Markdown in `src/content/pages/`,
and add a link in `NAV_LINKS` in `src/consts.ts`.

## Deploying

`npm run build` produces `dist/` — a plain folder of HTML/CSS/images that any
static host serves. No host is chosen yet; all of these work:

```bash
npm run build
rsync -avz dist/ user@server:/var/www/flagrantsystemerror/   # your own nginx/Apache
```

or drag `dist/` into Netlify / Cloudflare Pages / GitHub Pages (point their build
command at `npm run build` and their publish directory at `dist`).

Before the first real deploy, set `site` in `astro.config.mjs` to the final URL —
it's what makes `sitemap.xml` and the RSS feed use absolute links. If you serve
from a sub-path (e.g. a GitHub Pages project site), also set `base`.

## Re-importing from Notion

The original content came from Notion; two scripts can regenerate it (public
Notion API, no auth needed):

- `scripts/notion-export.py` — exports the Notion pages to Markdown and downloads
  their inline images.
- `scripts/fetch-covers.py` — downloads each page's cover into
  `public/images/covers/` and writes `heroImage`, `heroImagePosition`, and `icon`
  into the post frontmatter.

Slugs of already-published posts are pinned in each script's `SLUG_OVERRIDE` map so
existing URLs keep working. Day-to-day you don't need these — just edit Markdown.

## How the Notion look works

The styling comes from the `react-notion-x` stylesheet, vendored as
`src/styles/notion.css`, without shipping the Notion renderer:

- `src/plugins/rehype-notion-classes.mjs` stamps `notion-*` classes onto the HTML
  that Markdown compiles to (`<p>` → `.notion-text`, etc.) so the vendored CSS
  applies.
- `src/plugins/remark-notion-directives.mjs` turns the `:::` directives above into
  Notion-styled markup.
- `src/styles/notion-overrides.css` holds the small fixes that bridge Markdown's
  HTML to a stylesheet written for Notion's own markup (list/quote spacing, code
  blocks, figures). Kept separate so `notion.css` stays a clean vendor copy and can
  be updated from npm.

Dark mode follows the OS preference via `prefers-color-scheme`.
