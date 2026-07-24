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

Nothing else to wire up.

### Drafts

Set `draft: true` in a post's frontmatter to keep it out of the production build —
it gets no page, and is excluded from the archive, RSS, and sitemap. Drafts are
still viewable in `npm run dev`, so you can preview one before publishing. Remove
the flag (or set it to `false`) to publish.

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
draft: true                   # optional, hides from the production build
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

## Authoring in Notion

You can still write in Notion and import. Two scripts talk to the public Notion API
(no auth needed) and discover pages live from the posts database under the root
page, so a page you just created is picked up automatically. Run both from the repo
root:

```bash
python3 scripts/notion-export.py     # writes new posts to src/content/blog/ + images
python3 scripts/fetch-covers.py      # adds each post's cover + icon to its frontmatter
npm run build                        # the new post now appears everywhere
```

- **`scripts/notion-export.py`** converts each Notion page to Markdown and downloads
  its inline images. By default it **only writes posts that don't already exist**, so
  re-running after adding one Notion page touches just that page and leaves your
  edited files alone. Pass `--force` to re-export everything, or a slug fragment
  (e.g. `python3 scripts/notion-export.py kubernetes`) to target specific posts.
- **`scripts/fetch-covers.py`** downloads each page's cover into
  `public/images/covers/` and writes `heroImage`, `heroImagePosition`, and `icon`
  into the frontmatter. Re-running refreshes those fields for every post.

Slugs of already-published posts are pinned in each script's `SLUG_OVERRIDE` map so
existing URLs keep working; new pages get a slug from their title. Day-to-day you
don't need these — a plain Markdown file works just as well.

### Adding a page you created in Notion

1. Create and fill in the page in your Notion posts database.
2. `python3 scripts/notion-export.py` — the new page is discovered and written to
   `src/content/blog/<slug>.md`; existing posts are skipped.
3. `python3 scripts/fetch-covers.py` — pulls its cover and icon into the frontmatter.
4. `npm run dev` to preview, then `npm run build` to publish.

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
