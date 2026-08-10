#!/usr/bin/env python3
"""Export Flagrant System Error Notion posts -> Markdown + local images."""
import json, os, re, sys, time, urllib.error, urllib.request, urllib.parse, hashlib, collections, datetime

ROOT = "148786cf-a010-80f9-824f-f694cae70443"
OUT_MD  = os.environ.get("OUT_MD",  "src/content/blog")
OUT_IMG = os.environ.get("OUT_IMG", "public/images/posts")
OUT_PAGES = os.environ.get("OUT_PAGES", "src/content/pages")
IMG_PUBLIC_PREFIX = "/images/posts"   # how markdown references images

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

def api(ep, payload):
    r = urllib.request.Request("https://www.notion.so/api/v3/" + ep,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
    return json.load(open_with_rate_limit_retry(r))

def uuid(s):
    s = s.replace("-", "")
    return f"{s[0:8]}-{s[8:12]}-{s[12:16]}-{s[16:20]}-{s[20:32]}"

def load_page(pid):
    """Return {block_id: value} for a page, following chunk cursor."""
    blocks = {}
    cursor = {"stack": []}
    for _ in range(20):
        d = api("loadPageChunk", {"pageId": uuid(pid), "limit": 100,
                "cursor": cursor, "chunkNumber": 0, "verticalColumns": False})
        rm = d["recordMap"]["block"]
        for bid, rec in rm.items():
            v = rec.get("value", {})
            v = v.get("value", v)  # some shapes nest under value.value
            blocks[bid] = v
        cursor = d.get("cursor", {})
        if not cursor.get("stack"):
            break
    return blocks

# ---------- rich text ----------
def rich(arr):
    if not arr: return ""
    out = []
    for seg in arr:
        text = seg[0]
        fmts = seg[1] if len(seg) > 1 else []
        # inline equation: marker char carries an ["e", latex] format
        eq = next((f[1] for f in (fmts or []) if f[0] == "e"), None)
        if eq is not None:
            out.append(f"${eq}$")
            continue
        link = None; code = bold = ital = strike = False
        for f in fmts or []:
            k = f[0]
            if k == "b": bold = True
            elif k == "i": ital = True
            elif k == "s": strike = True
            elif k == "c": code = True
            elif k == "a": link = f[1]
        t = text
        if code:
            t = f"`{t}`"
        elif bold or ital or strike:
            # Notion often includes trailing/leading spaces inside a styled run
            # (e.g. "Figure 1, " bold). CommonMark won't close markers that hug
            # whitespace, so keep the spaces outside the markers.
            lead = t[: len(t) - len(t.lstrip())]
            trail = t[len(t.rstrip()):]
            core = t.strip()
            if core:
                if bold: core = f"**{core}**"
                if ital: core = f"*{core}*"
                if strike: core = f"~~{core}~~"
                t = f"{lead}{core}{trail}"
        if link:
            t = f"[{t}]({link})"
        out.append(t)
    return "".join(out)

def title_of(v):
    return "".join(s[0] for s in v.get("properties", {}).get("title", [[""]]) if s)

# ---------- image handling ----------
downloaded = {}
def local_image(src, block_id):
    if not src: return None
    # Raw S3 URLs are expired, and newer `attachment:<id>:<name>` refs aren't
    # URLs at all; both resolve through Notion's signing proxy, keyed to the
    # owning block id. This is what react-notion-x does.
    if ("amazonaws.com" in src) or src.startswith("attachment:"):
        enc = urllib.parse.quote(src, safe="")
        src = f"https://www.notion.so/image/{enc}?table=block&id={block_id}&cache=v2"
    elif src.startswith("/image"):
        src = "https://www.notion.so" + src
    if src in downloaded:
        return downloaded[src]
    ext = ".png"
    m = re.search(r"\.(png|jpe?g|gif|webp|svg)", src.lower())
    if m: ext = "." + m.group(1).replace("jpeg", "jpg")
    name = hashlib.md5((block_id + src).encode()).hexdigest()[:12] + ext
    path = os.path.join(OUT_IMG, name)
    os.makedirs(OUT_IMG, exist_ok=True)
    try:
        req = urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0"})
        data = open_with_rate_limit_retry(req).read()
        with open(path, "wb") as f: f.write(data)
        ref = f"{IMG_PUBLIC_PREFIX}/{name}"
        downloaded[src] = ref
        print(f"    img {len(data)//1024}KB -> {ref}", file=sys.stderr)
        return ref
    except Exception as e:
        print(f"    !! image failed {src[:60]}: {e}", file=sys.stderr)
        downloaded[src] = None
        return None

def source_url(v):
    props = v.get("properties", {})
    fmt = v.get("format", {})
    if fmt.get("display_source"): return fmt["display_source"]
    s = props.get("source")
    if s: return s[0][0]
    return None

# ---------- block -> markdown ----------
def render_blocks(ids, blocks, depth=0):
    lines = []
    num = 0
    for bid in ids:
        v = blocks.get(bid)
        if not v: continue
        t = v.get("type")
        props = v.get("properties", {})
        text = rich(props.get("title", []))
        children = v.get("content", [])
        if t != "numbered_list": num = 0

        if t == "text":
            # A text block that is nothing but a single inline equation was an
            # equation placed on its own line: promote to display math so it
            # renders centered, the way Notion shows a block equation.
            s = text.strip()
            if s.startswith("$") and s.endswith("$") and not s.startswith("$$") and s.count("$") == 2:
                lines.append(f"$$\n{s[1:-1].strip()}\n$$")
            else:
                lines.append(text)
            lines.append("")
        elif t == "header":
            lines.append(f"# {text}"); lines.append("")
        elif t == "sub_header":
            lines.append(f"## {text}"); lines.append("")
        elif t == "sub_sub_header":
            lines.append(f"### {text}"); lines.append("")
        elif t == "bulleted_list":
            lines.append("  " * depth + f"- {text}")
            if children: lines += render_blocks(children, blocks, depth + 1)
            if depth == 0: lines.append("")
        elif t == "numbered_list":
            num += 1
            lines.append("  " * depth + f"{num}. {text}")
            if children: lines += render_blocks(children, blocks, depth + 1)
            if depth == 0: lines.append("")
        elif t == "to_do":
            checked = props.get("checked", [["No"]])[0][0] == "Yes"
            lines.append(f"- [{'x' if checked else ' '}] {text}");
            if depth == 0: lines.append("")
        elif t == "quote":
            for ln in (text or "").split("\n"):
                lines.append(f"> {ln}")
            lines.append("")
        elif t == "callout":
            icon = (v.get("format", {}) or {}).get("page_icon", "💡")
            body = text.replace("\n", " ")
            lines.append(f':::callout{{icon="{icon}"}}')
            lines.append(body)
            if children: lines += render_blocks(children, blocks, depth)
            lines.append(":::"); lines.append("")
        elif t == "code":
            lang = (props.get("language", [["text"]])[0][0] or "text").lower()
            lang = {"plain text": "text"}.get(lang, lang)
            code = props.get("title", [[""]])
            raw = "".join(s[0] for s in code)
            lines.append(f"```{lang}"); lines.append(raw); lines.append("```"); lines.append("")
        elif t == "image":
            ref = local_image(source_url(v), bid)
            cap = rich(props.get("caption", [])) if props.get("caption") else ""
            if ref:
                alt = re.sub(r"[*_`\[\]]", "", cap).replace('"', "'").strip()
                attr = f'src="{ref}"' + (f' alt="{alt}"' if alt else "")
                lines.append(f":::figure{{{attr}}}")
                if cap:
                    lines.append(cap)
                lines.append(":::")
                lines.append("")
        elif t == "divider":
            lines.append("---"); lines.append("")
        elif t == "equation":
            eq = "".join(s[0] for s in props.get("title", [[""]]))
            lines.append(f"$$\n{eq}\n$$"); lines.append("")
        elif t in ("bookmark", "embed", "video", "tweet"):
            url = source_url(v) or (props.get("link", [[""]])[0][0])
            cap = rich(props.get("caption", [])) if props.get("caption") else ""
            if t == "bookmark":
                bt = rich(props.get("title", [])) or url
                lines.append(f':::bookmark{{url="{url}"}}')
                lines.append(bt)
                lines.append(":::")
            else:
                lines.append(f':::embed{{url="{url}"}}')
                if cap: lines.append(cap)
                lines.append(":::")
            lines.append("")
        elif t in ("column_list", "column"):
            if children: lines += render_blocks(children, blocks, depth)
        elif t in ("collection_view", "collection_view_page", "page"):
            continue  # skip nested DBs / child page links inside a post
        else:
            if text:
                lines.append(text); lines.append("")
    return lines

def slugify(s):
    s = re.sub(r"[^\w\s-]", "", s.lower()).strip()
    return re.sub(r"[\s_]+", "-", s)

def export_page(pid, slug_hint=None):
    blocks = load_page(pid)
    root = blocks.get(uuid(pid)) or blocks.get(pid)
    if not root:
        # find the page block
        for b, v in blocks.items():
            if v.get("type") == "page":
                root = v; break
    title = title_of(root)
    content_ids = root.get("content", [])
    body = "\n".join(render_blocks(content_ids, blocks)).rstrip() + "\n"
    return title, body, root

def ymd(ms):
    return datetime.datetime.fromtimestamp(ms / 1000, datetime.timezone.utc).strftime("%Y-%m-%d")

def iso(ms):
    return datetime.datetime.fromtimestamp(ms / 1000, datetime.timezone.utc).isoformat()

def stored_last_edited_ms(path):
    """Read notionLastEdited out of an existing .md's front matter, as epoch ms.
    Returns None if the file has no such field (e.g. exported before this field
    existed) so callers can fall back to leaving it untouched."""
    try:
        with open(path) as f:
            lines = f.read().splitlines()
    except OSError:
        return None
    if not lines or lines[0].strip() != "---":
        return None
    for ln in lines[1:]:
        if ln.strip() == "---":
            break
        m = re.match(r'\s*notionLastEdited:\s*"?([^"]+)"?\s*$', ln)
        if m:
            try:
                dt = datetime.datetime.fromisoformat(m.group(1))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=datetime.timezone.utc)
                return int(dt.timestamp() * 1000)
            except ValueError:
                return None
    return None

def public_of(root, pubid):
    """Read the Notion 'Public' checkbox (schema property id `pubid`) off a page
    block. Notion is the source of truth for whether a post is published."""
    if not pubid:
        return None
    val = root.get("properties", {}).get(pubid)
    if not val:
        return False  # unchecked boxes are simply absent from properties
    return val[0][0] == "Yes"

def first_sentence(body):
    for ln in body.splitlines():
        ln = ln.strip()
        if not ln or ln.startswith(("#", "!", ":", ">", "-", "`", "$", "|")):
            continue
        plain = re.sub(r"[*_`\[\]()]|\((?:https?:)?[^)]*\)", "", ln)
        plain = re.sub(r"\]\([^)]*\)", "", plain)
        plain = re.sub(r"[*_`]", "", plain)
        return (plain[:157] + "…") if len(plain) > 158 else plain
    return ""

def yaml_escape(s):
    return s.replace('\\', '\\\\').replace('"', '\\"')

def write_post(slug, title, body, root, out_dir, is_public=None):
    pub = ymd(root["created_time"])
    upd = ymd(root["last_edited_time"])
    desc = first_sentence(body)
    path = os.path.join(out_dir, slug + ".md")
    fm = ["---", f'title: "{yaml_escape(title)}"', f'pubDate: {pub}']
    if upd != pub:
        fm.append(f'updatedDate: {upd}')
    if desc:
        fm.append(f'description: "{yaml_escape(desc)}"')
    # Notion's 'Public' checkbox drives publication; re-export always reflects
    # it, overwriting any local edit. Omitted for pages outside the DB.
    if is_public is not None:
        fm.append(f'public: {"true" if is_public else "false"}')
    # Full-precision revision stamp used to detect Notion edits on re-run.
    # (updatedDate above is day-resolution and omitted when it equals pubDate,
    # so it can't serve as a reliable comparison key.)
    fm.append(f'notionLastEdited: "{iso(root["last_edited_time"])}"')
    fm += ["---", ""]
    os.makedirs(out_dir, exist_ok=True)
    open(path, "w").write("\n".join(fm) + body)
    print(f"WROTE {out_dir}/{slug}.md  pub={pub}", file=sys.stderr)

DEMO = ("nextjs-notion-starter-kit", "example-article",
        "example-page-using-a-custom-slug", "flagrant-system-error")

# Preserve the live site's URLs so inbound links keep working.
SLUG_OVERRIDE = {
    "Probability: Fundamentals": "probability-fundamentals",
    "Experimenting with Kubernetes": "kubernetes-homelab",
    "The Pyramid Principle for Writing": "pyramid-principle",
    "Review of Naming Things by Tom Benner": "naming-things",
    "Staff Engineer Book Review, Part 1": "staff-engineer-book-review-part-1",
    "Category Theory: Programming Language Semantics": "language-semantics",
    "Category Theory: What Is A Category?": "category-theory",
}

def bval(rec):
    v = rec.get("value", {})
    return v.get("value", v)

def fetch_meta(pid):
    """Cheap title + revision-time lookup (one chunk) so we can decide to skip
    before doing the full render, which would otherwise re-download the page's
    images. Returns (title, last_edited_ms)."""
    d = api("loadPageChunk", {"pageId": uuid(pid), "limit": 1,
            "cursor": {"stack": []}, "chunkNumber": 0, "verticalColumns": False})
    root = d["recordMap"]["block"].get(uuid(pid))
    if not root:
        return "", None
    v = bval(root)
    return title_of(v), v.get("last_edited_time")

def discover_post_ids():
    """Query the posts database under the root page for its current page IDs,
    so newly-created Notion pages are picked up automatically. Also resolves the
    'Public' checkbox's schema property id (opaque and collection-specific), so
    callers can read it off each page's root block."""
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
    schema = bval(next(iter(res["recordMap"]["collection"].values()))).get("schema", {})
    pubid = next((pid for pid, s in schema.items() if s.get("name") == "Public"), None)
    ids = [b for b, r in res["recordMap"]["block"].items() if bval(r).get("type") == "page"]
    return ids, pubid

def main():
    # Flags: --force re-exports pages whose .md already exists; a bare word
    # filters to slugs containing it. By default only missing pages are written,
    # so re-running after adding one Notion page touches just that page.
    args = sys.argv[1:]
    force = "--force" in args
    only = next((a for a in args if not a.startswith("-")), None)

    post_ids, pubid = discover_post_ids()
    for pid in post_ids:
        title, edited_ms = fetch_meta(pid)
        if slugify(title) in DEMO:
            continue
        slug = SLUG_OVERRIDE.get(title, slugify(title))
        if only and only not in slug:
            continue
        path = os.path.join(OUT_MD, slug + ".md")
        if os.path.exists(path) and not force:
            stored = stored_last_edited_ms(path)
            if stored is None:
                print(f"exists (no revision stamp), skipping {slug}.md "
                      f"(re-run with --force to add one)", file=sys.stderr)
                continue
            if edited_ms is None or edited_ms <= stored:
                print(f"up to date, skipping {slug}.md", file=sys.stderr)
                continue
            print(f"NOTION NEWER, re-exporting {slug}.md "
                  f"({iso(stored)} -> {iso(edited_ms)})", file=sys.stderr)
        # Full render (downloads images) only for pages we will actually write.
        _, body, root = export_page(pid)
        write_post(slug, title, body, root, OUT_MD, is_public=public_of(root, pubid))

    # Standalone pages (About, Colophon) — child pages of the root, not in the DB
    for pid, slug, page_title in [("148786cf-a010-81c2-b3a0-fc4b046a0351", "about", "About"),
                                  ("148786cf-a010-8033-9b06-ee70f38ecb9d", "colophon", "Colophon")]:
        if only and only not in slug:
            continue
        path = os.path.join(OUT_PAGES, slug + ".md")
        if os.path.exists(path) and not force:
            stored = stored_last_edited_ms(path)
            _, edited_ms = fetch_meta(pid)
            if stored is None:
                print(f"exists (no revision stamp), skipping {slug}.md "
                      f"(re-run with --force to add one)", file=sys.stderr)
                continue
            if edited_ms is None or edited_ms <= stored:
                print(f"up to date, skipping {slug}.md", file=sys.stderr)
                continue
            print(f"NOTION NEWER, re-exporting {slug}.md "
                  f"({iso(stored)} -> {iso(edited_ms)})", file=sys.stderr)
        try:
            title, body, root = export_page(pid)
            write_post(slug, page_title, body, root, OUT_PAGES)
        except Exception as e:
            print(f"!! page {slug} failed: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
