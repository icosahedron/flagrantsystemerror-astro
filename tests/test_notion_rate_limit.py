import io
import importlib.util
import json
import os
from contextlib import redirect_stdout
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError


SCRIPTS = ("fetch-covers.py", "notion-export.py")


def load_script(script_name):
    path = Path(__file__).parents[1] / "scripts" / script_name
    spec = importlib.util.spec_from_file_location(script_name.replace("-", "_"), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rate_limit_error(retry_after=None):
    headers = {} if retry_after is None else {"Retry-After": retry_after}
    return HTTPError(
        "https://www.notion.so/api/v3/loadPageChunk",
        429,
        "Too Many Requests",
        headers,
        None,
    )


class NotionRateLimitTests(unittest.TestCase):
    def test_fetch_covers_reuses_a_nonempty_cached_file(self):
        module = load_script("fetch-covers.py")
        url = "https://example.com/cover.jpg"
        key = "page-id-and-cover-reference"

        with tempfile.TemporaryDirectory() as directory:
            module.OUT_IMG = directory
            name = module.hashlib.md5(key.encode()).hexdigest()[:12] + ".jpg"
            cached_file = Path(directory) / name
            cached_file.write_bytes(b"cached image")

            with patch.object(
                module.urllib.request,
                "urlopen",
                side_effect=AssertionError("network requested for cached cover"),
            ):
                hero, size, cached = module.download(url, key)

        self.assertEqual(hero, f"{module.IMG_PREFIX}/{name}")
        self.assertEqual(size, len(b"cached image"))
        self.assertTrue(cached)

    def test_fetch_covers_replaces_an_empty_cached_file(self):
        module = load_script("fetch-covers.py")
        url = "https://example.com/cover.jpg"
        key = "page-id-and-cover-reference"
        response = unittest.mock.MagicMock()
        response.read.return_value = b"fresh image"

        with tempfile.TemporaryDirectory() as directory:
            module.OUT_IMG = directory
            name = module.hashlib.md5(key.encode()).hexdigest()[:12] + ".jpg"
            cached_file = Path(directory) / name
            cached_file.touch()

            with patch.object(module.urllib.request, "urlopen", return_value=response):
                hero, size, cached = module.download(url, key)

            self.assertEqual(cached_file.read_bytes(), b"fresh image")

        self.assertEqual(hero, f"{module.IMG_PREFIX}/{name}")
        self.assertEqual(size, len(b"fresh image"))
        self.assertFalse(cached)

    def test_fetch_covers_ignores_expiring_s3_query_parameters_in_cache_key(self):
        module = load_script("fetch-covers.py")
        first = "https://s3.us-east-1.amazonaws.com/bucket/cover.png?X-Amz-Date=one"
        second = "https://s3.us-east-1.amazonaws.com/bucket/cover.png?X-Amz-Date=two"
        versioned = "https://s3.us-east-1.amazonaws.com/bucket/cover.png?version=two"

        self.assertEqual(module.canonical_source(first), module.canonical_source(second))
        self.assertNotEqual(module.canonical_source(first), module.canonical_source(versioned))

    def test_fetch_covers_reuses_cache_when_s3_signature_changes(self):
        module = load_script("fetch-covers.py")
        first = "https://s3.us-east-1.amazonaws.com/bucket/cover.png?X-Amz-Date=one"
        second = "https://s3.us-east-1.amazonaws.com/bucket/cover.png?X-Amz-Date=two"
        response = unittest.mock.MagicMock()
        response.read.return_value = b"cached cover"

        with tempfile.TemporaryDirectory() as directory:
            module.OUT_IMG = directory
            key1 = "page-id" + module.canonical_source(first)
            key2 = "page-id" + module.canonical_source(second)
            with patch.object(module.urllib.request, "urlopen", return_value=response):
                first_ref, first_size, first_cached = module.download(first, key1)
            with patch.object(
                module.urllib.request,
                "urlopen",
                side_effect=AssertionError("network requested for signed URL refresh"),
            ):
                second_ref, second_size, second_cached = module.download(second, key2)

        self.assertEqual((second_ref, second_size), (first_ref, first_size))
        self.assertFalse(first_cached)
        self.assertTrue(second_cached)

    def test_fetch_covers_process_reuses_cache_when_s3_signature_changes(self):
        module = load_script("fetch-covers.py")
        pid = "12345678123412341234123456789012"
        first = "https://s3.us-east-1.amazonaws.com/bucket/cover.png?X-Amz-Date=one"
        second = "https://s3.us-east-1.amazonaws.com/bucket/cover.png?X-Amz-Date=two"
        response = unittest.mock.MagicMock()
        response.read.return_value = b"cached cover"

        def page_response(raw):
            return {"recordMap": {"block": {module.uuid(pid): {
                "value": {"value": {"format": {"page_cover": raw}}},
            }}}}

        with tempfile.TemporaryDirectory() as directory:
            module.OUT_IMG = directory
            post = Path(directory) / "post.md"
            post.write_text("---\ntitle: Post\npubDate: 2026-01-01\n---\n", encoding="utf-8")
            with patch.object(module, "api", return_value=page_response(first)), \
                 patch.object(module.urllib.request, "urlopen", return_value=response):
                first_output = io.StringIO()
                with redirect_stdout(first_output):
                    module.process(pid, post)
            with patch.object(module, "api", return_value=page_response(second)), \
                 patch.object(
                     module.urllib.request,
                     "urlopen",
                     side_effect=AssertionError("network requested for signed URL refresh"),
                 ):
                second_output = io.StringIO()
                with redirect_stdout(second_output):
                    module.process(pid, post)
            post_contents = post.read_text(encoding="utf-8")

        self.assertIn("heroImage:", post_contents)
        self.assertIn("cover=downloaded", first_output.getvalue())
        self.assertIn("cover=cached", second_output.getvalue())

    def test_image_writes_do_not_leave_a_partial_cache_file(self):
        for script_name in SCRIPTS:
            with self.subTest(script=script_name):
                module = load_script(script_name)
                with tempfile.TemporaryDirectory() as directory:
                    module.OUT_IMG = directory
                    path = Path(directory) / "image.png"
                    with patch.object(module.os, "replace", side_effect=OSError("interrupted")):
                        with self.assertRaises(OSError):
                            module.write_atomically(path, b"partial image")

                    self.assertFalse(path.exists())

    def test_rich_rewrites_known_internal_notion_page_links(self):
        module = load_script("notion-export.py")
        page_id = "3bb786cfa01080e78d4ec4a96b8b7368"
        module.INTERNAL_PAGE_URLS = {page_id: "/conditional-compilation-in-lean/"}

        self.assertEqual(
            module.rich([["Conditional Compilation in Lean", [["a", f"/p/{page_id}?pvs=25"]]]]),
            "[Conditional Compilation in Lean](/conditional-compilation-in-lean/)",
        )
        self.assertEqual(
            module.rich([["Lean", [["a", "https://lean-lang.org"]]]]),
            "[Lean](https://lean-lang.org)",
        )

    def test_notion_export_reuses_a_nonempty_cached_image(self):
        module = load_script("notion-export.py")
        src = "https://example.com/diagram.png"
        block_id = "block-id"

        with tempfile.TemporaryDirectory() as directory:
            module.OUT_IMG = directory
            module.downloaded = {}
            name = module.hashlib.md5((block_id + src).encode()).hexdigest()[:12] + ".png"
            cached = Path(directory) / name
            cached.write_bytes(b"cached image")

            with patch.object(
                module.urllib.request,
                "urlopen",
                side_effect=AssertionError("network requested for cached image"),
            ):
                ref = module.local_image(src, block_id)

        self.assertEqual(ref, f"{module.IMG_PUBLIC_PREFIX}/{name}")

    def test_notion_export_reuses_signed_s3_image_across_module_loads(self):
        first_module = load_script("notion-export.py")
        second_module = load_script("notion-export.py")
        block_id = "block-id"
        first = "https://s3.us-east-1.amazonaws.com/bucket/diagram.png?X-Amz-Date=one"
        second = "https://s3.us-east-1.amazonaws.com/bucket/diagram.png?X-Amz-Date=two"
        response = unittest.mock.MagicMock()
        response.read.return_value = b"cached image"

        with tempfile.TemporaryDirectory() as directory:
            first_module.OUT_IMG = directory
            first_module.downloaded = {}
            with patch.object(first_module.urllib.request, "urlopen", return_value=response):
                first_ref = first_module.local_image(first, block_id)

            second_module.OUT_IMG = directory
            second_module.downloaded = {}
            with patch.object(
                second_module.urllib.request,
                "urlopen",
                side_effect=AssertionError("network requested for signed URL refresh"),
            ):
                second_ref = second_module.local_image(second, block_id)

        self.assertEqual(second_ref, first_ref)

    def test_notion_export_replaces_an_empty_cached_image(self):
        module = load_script("notion-export.py")
        src = "https://example.com/diagram.png"
        block_id = "block-id"
        response = unittest.mock.MagicMock()
        response.read.return_value = b"fresh image"

        with tempfile.TemporaryDirectory() as directory:
            module.OUT_IMG = directory
            module.downloaded = {}
            name = module.hashlib.md5((block_id + src).encode()).hexdigest()[:12] + ".png"
            cached = Path(directory) / name
            cached.touch()

            with patch.object(module.urllib.request, "urlopen", return_value=response):
                ref = module.local_image(src, block_id)

            self.assertEqual(cached.read_bytes(), b"fresh image")

        self.assertEqual(ref, f"{module.IMG_PUBLIC_PREFIX}/{name}")

    def test_fetch_covers_honors_content_directory_overrides(self):
        with patch.dict(os.environ, {
            "BLOG_DIR": "/tmp/fse-notion/blog",
            "PAGES_DIR": "/tmp/fse-notion/pages",
        }):
            module = load_script("fetch-covers.py")

        self.assertEqual(module.BLOG_DIR, "/tmp/fse-notion/blog")
        self.assertEqual(module.PAGES_DIR, "/tmp/fse-notion/pages")

    def test_api_retries_429_after_retry_after_delay(self):
        for script_name in SCRIPTS:
            with self.subTest(script=script_name):
                module = load_script(script_name)
                response = unittest.mock.MagicMock()
                response.read.return_value = json.dumps({"ok": True}).encode()
                rate_limited = rate_limit_error("12")

                with patch.object(module.urllib.request, "urlopen", side_effect=[rate_limited, response]), \
                     patch.object(module.time, "sleep") as sleep:
                    self.assertEqual(module.api("loadPageChunk", {}), {"ok": True})

                sleep.assert_called_once_with(12.0)

    def test_api_uses_a_minute_when_retry_after_is_missing(self):
        for script_name in SCRIPTS:
            with self.subTest(script=script_name):
                module = load_script(script_name)
                response = unittest.mock.MagicMock()
                response.read.return_value = json.dumps({"ok": True}).encode()
                rate_limited = rate_limit_error()

                with patch.object(module.urllib.request, "urlopen", side_effect=[rate_limited, response]), \
                     patch.object(module.time, "sleep") as sleep:
                    self.assertEqual(module.api("loadPageChunk", {}), {"ok": True})

                sleep.assert_called_once_with(60.0)

    def test_api_does_not_retry_non_rate_limit_errors(self):
        for script_name in SCRIPTS:
            with self.subTest(script=script_name):
                module = load_script(script_name)
                error = HTTPError("https://www.notion.so", 500, "Server Error", {}, None)

                with patch.object(module.urllib.request, "urlopen", side_effect=error), \
                     patch.object(module.time, "sleep") as sleep:
                    with self.assertRaises(HTTPError):
                        module.api("loadPageChunk", {})

                sleep.assert_not_called()
                error.close()

    def test_api_stops_after_six_rate_limit_responses(self):
        for script_name in SCRIPTS:
            with self.subTest(script=script_name):
                module = load_script(script_name)
                errors = [rate_limit_error() for _ in range(6)]

                with patch.object(module.urllib.request, "urlopen", side_effect=errors), \
                     patch.object(module.time, "sleep") as sleep:
                    with self.assertRaises(HTTPError):
                        module.api("loadPageChunk", {})

                self.assertEqual(sleep.call_count, 5)
                errors[-1].close()


if __name__ == "__main__":
    unittest.main()
