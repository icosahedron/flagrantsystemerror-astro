set shell := ["bash", "-eu", "-o", "pipefail", "-c"]

notion_dir := "/tmp/fse-notion"

default: build

# Retrieve the current Notion pages into a persistent staging directory.
notion:
    OUT_MD={{ notion_dir }}/blog OUT_PAGES={{ notion_dir }}/pages python3 scripts/notion-export.py
    BLOG_DIR={{ notion_dir }}/blog python3 scripts/fetch-covers.py

[private]
check-tools:
    #!/usr/bin/env bash
    set -eu
    missing=()
    for tool in fd verso recto; do
        command -v "$tool" >/dev/null 2>&1 || missing+=("$tool")
    done
    ((${#missing[@]} == 0)) || {
        printf 'Missing required tools: %s\n' "${missing[*]}" >&2
        exit 1
    }

# Weave every tagged blog post from fragments found in the code checkout.
# Woven posts retain their paths below src/content (for example,
# src/content/blog/lean-roguelike-part-2.md).
knit: check-tools
    #!/usr/bin/env bash
    set -euo pipefail
    repo_root="$(pwd -P)"
    stage={{ notion_dir }}
    mkdir -p "$stage"
    fd -e lean -e c -a -t f . "$repo_root/code" > "$stage/verso.lst"
    [[ -s "$stage/verso.lst" ]] || { echo 'No source files found under code/' >&2; exit 1; }
    (
        cd "$stage"
        fd -e md -t f . blog > recto.lst
        [[ -s recto.lst ]] || { echo 'No staged blog posts found under' "$stage/blog" >&2; exit 1; }
        verso "@$stage/verso.lst" | recto "$repo_root/src/content" @recto.lst
    )
    pages=()
    while IFS= read -r -d '' page; do pages+=("$page"); done < <(find "$stage/pages" -type f -name '*.md' -print0)
    ((${#pages[@]})) && cp "${pages[@]}" "$repo_root/src/content/pages/"

# Build the static Astro site after refreshing content and knitted excerpts.
build: notion knit
    npm run build
