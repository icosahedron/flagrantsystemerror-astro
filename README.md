# Flagrant System Error

The blog at [flagrantsystemerror.com](https://flagrantsystemerror.com), built with
[Astro](https://astro.build) as a fully static site. Content lives as Markdown in
this repo; there is no server and no build-time dependency on Notion.

## How it works

Posts are Markdown files in `src/content/blog/`. They render with the
**look and feel of Notion** without shipping the Notion renderer:

- `src/styles/notion.css` — the `react-notion-x` stylesheet, vendored. It also
  follows the OS light/dark preference via `prefers-color-scheme`.
- `src/plugins/rehype-notion-classes.mjs` — stamps `notion-*` class names onto
  the HTML that Markdown compiles to (`<p>` → `.notion-text`, etc.) so the
  vendored CSS applies.
- `src/plugins/remark-notion-directives.mjs` — renders `:::callout`,
  `:::bookmark`, and `:::embed` container directives into Notion-styled markup.
- Math (`$inline$` and `$$block$$`) renders with KaTeX.

## Develop

```bash
npm install
npm run dev        # http://localhost:4321
npm run build      # type-checks, then outputs static site to dist/
npm run preview    # serve the built dist/ locally
```

## Deploy

`dist/` is a plain static site — upload it anywhere that serves files:

```bash
npm run build
rsync -avz dist/ user@server:/var/www/flagrantsystemerror/
```

## Writing a new post

Add a Markdown file to `src/content/blog/`. The filename is the URL slug.

```markdown
---
title: "My Post Title"
pubDate: 2026-07-24
description: "One-line summary for the index and RSS."
---

Body goes here.
```

`src/content/pages/` holds standalone pages (About, Colophon), authored the same way.

## Importing from Notion

`scripts/notion-export.py` re-exports the original Notion pages to Markdown and
downloads their images. `scripts/fetch-covers.py` downloads each page's Notion
cover image into `public/images/covers/` and injects `heroImage` +
`heroImagePosition` (the crop focal point) into the post frontmatter. Both talk
to Notion's public API and need no auth for a public page. Slugs of
already-published posts are pinned in each script's `SLUG_OVERRIDE` map so
existing URLs keep working.
