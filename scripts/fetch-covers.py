#!/usr/bin/env python3
"""Fetch each post's Notion page cover image and inject heroImage +
heroImagePosition into the corresponding Markdown frontmatter. Idempotent:
re-running replaces the same fields. Bodies are left untouched."""
import json, os, re, sys, time, urllib.error, urllib.request, urllib.parse, hashlib

OUT_IMG = "public/images/covers"
IMG_PREFIX = "/images/covers"
BLOG_DIR = os.environ.get("BLOG_DIR", "src/content/blog")

# Same slug pinning the exporter uses, so covers land on the right files.
SLUG_OVERRIDE = {
    "Probability: Fundamentals": "probability-fundamentals",
    "Experimenting with Kubernetes": "kubernetes-homelab",
    "The Pyramid Principle for Writing": "pyramid-principle",
    "Review of Naming Things by Tom Benner": "naming-things",
    "Staff Engineer Book Review, Part 1": "staff-engineer-book-review-part-1",
    "Category Theory: Programming Language Semantics": "language-semantics",
    "Category Theory: What Is A Category?": "category-theory",
}
DEMO = ("Next.js Notion Starter Kit", "Example article",
        "Example page using a custom slug", "Flagrant System Error")

def open_with_rate_limit_retry(request):
    for attempt in range(6):
        try:
            return urllib.request.urlopen(request)
        except urllib.error.HTTPError as error:
            if error.code != 429 or attempt == 5:
                raise
            retry_after = error.headers.get("Retry-After") if error.headers else None
            try:
                delay = max(0.0, float(retry_after))
            except (TypeError, ValueError):
                delay = 60.0
            error.close()
            print(f"Notion rate-limited; retrying in {delay:g}s", file=sys.stderr)
            time.sleep(delay)

def api(ep, p):
    r = urllib.request.Request("https://www.notion.so/api/v3/" + ep,
        data=json.dumps(p).encode(),
        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
    return json.load(open_with_rate_limit_retry(r))

def uuid(s):
    s = s.replace("-", "")
    return f"{s[0:8]}-{s[8:12]}-{s[12:16]}-{s[16:20]}-{s[20:32]}"

def slugify(s):
    s = re.sub(r"[^\w\s-]", "", s.lower()).strip()
    return re.sub(r"[\s_]+", "-", s)

def cover_src(raw, pid):
    if raw.startswith("/images/"):
        return "https://www.notion.so" + raw
    # Expired S3 URLs and newer `attachment:<id>:<name>` refs both resolve
    # through Notion's image proxy, keyed to the owning block id.
    if "amazonaws.com" in raw or "notion-static" in raw or raw.startswith("attachment:"):
        return f"https://www.notion.so/image/{urllib.parse.quote(raw, safe='')}?table=block&id={pid}&cache=v2"
    if "images.unsplash.com" in raw and "w=" not in raw:
        return raw + "&w=1600"
    return raw

def download(url, key):
    ext = ".jpg"
    m = re.search(r"\.(png|jpe?g|gif|webp)", url.lower())
    if m: ext = "." + m.group(1).replace("jpeg", "jpg")
    name = hashlib.md5(key.encode()).hexdigest()[:12] + ext
    os.makedirs(OUT_IMG, exist_ok=True)
    path = os.path.join(OUT_IMG, name)
    data = open_with_rate_limit_retry(
        urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    ).read()
    open(path, "wb").write(data)
    return f"{IMG_PREFIX}/{name}", len(data)

def set_frontmatter(path, hero, pos, icon):
    s = open(path, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n", s, re.S)
    if not m:
        print("  !! no frontmatter in", path); return
    fm = m.group(1)
    # Only rewrite the fields we actually resolved. A transient empty response
    # from Notion must never strip a cover/icon that's already in the file.
    if hero:
        for key in ("heroImage", "heroImagePosition"):
            fm = re.sub(rf"\n?{key}:.*", "", fm)
        fm += f'\nheroImage: "{hero}"'
        if pos is not None:
            fm += f"\nheroImagePosition: {pos}"
    if icon:
        fm = re.sub(r"\n?icon:.*", "", fm)
        fm += f'\nicon: "{icon}"'
    open(path, "w", encoding="utf-8").write(f"---\n{fm}\n---\n" + s[m.end():])

def process(pid, path):
    d = api("loadPageChunk", {"pageId": uuid(pid), "limit": 2,
            "cursor": {"stack": []}, "chunkNumber": 0, "verticalColumns": False})
    root = d["recordMap"]["block"].get(uuid(pid))
    if not root: return
    v = root.get("value", {}).get("value") or root.get("value", {})
    fmt = v.get("format", {}) or {}
    raw = fmt.get("page_cover")
    # Only emoji icons are supported inline; image icons are skipped.
    icon = fmt.get("page_icon")
    if icon and icon.startswith("http"):
        icon = None
    hero = pos = None
    if raw:
        hero, _ = download(cover_src(raw, uuid(pid)), f"{pid}{raw}")
        pos = fmt.get("page_cover_position")
    set_frontmatter(path, hero, pos, icon)
    print(f"  {os.path.basename(path):40} icon={icon!s:4} pos={pos!s:6} cover={'yes' if hero else 'no'}")

ROOT = "148786cf-a010-80f9-824f-f694cae70443"

def bval(rec):
    v = rec.get("value", {})
    return v.get("value", v)

def discover_post_ids():
    d = api("loadPageChunk", {"pageId": uuid(ROOT), "limit": 50,
            "cursor": {"stack": []}, "chunkNumber": 0, "verticalColumns": False})
    blocks = d["recordMap"]["block"]
    cvid = next(b for b, r in blocks.items() if bval(r).get("type") == "collection_view")
    cv = bval(blocks[cvid])
    colid, viewid = cv["collection_id"], cv["view_ids"][0]
    res = api("queryCollection", {"collection": {"id": colid},
        "collectionView": {"id": viewid},
        "loader": {"type": "reducer", "reducers": {"c": {"type": "results", "limit": 100}},
                   "searchQuery": "", "userTimeZone": "UTC"}})
    return [b for b, r in res["recordMap"]["block"].items() if bval(r).get("type") == "page"]

def main():
    ids = discover_post_ids()
    # Blog posts (keyed by title -> slug).
    for pid in ids:
        d = api("loadPageChunk", {"pageId": uuid(pid), "limit": 1,
                "cursor": {"stack": []}, "chunkNumber": 0, "verticalColumns": False})
        v = (d["recordMap"]["block"].get(uuid(pid)) or {}).get("value", {})
        v = v.get("value", v)
        if v.get("type") != "page":
            continue
        title = "".join(x[0] for x in v.get("properties", {}).get("title", [[""]]) if x)
        if title in DEMO:
            continue
        slug = SLUG_OVERRIDE.get(title, slugify(title))
        path = os.path.join(BLOG_DIR, slug + ".md")
        if os.path.exists(path):
            process(pid, path)
    # Standalone pages.
    for pid, name in [("148786cf-a010-81c2-b3a0-fc4b046a0351", "about"),
                      ("148786cf-a010-8033-9b06-ee70f38ecb9d", "colophon")]:
        path = os.path.join("src/content/pages", name + ".md")
        if os.path.exists(path):
            process(pid, path)

if __name__ == "__main__":
    main()
