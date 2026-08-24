import importlib.util
import json
import os
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
            cached = Path(directory) / name
            cached.write_bytes(b"cached image")

            with patch.object(
                module.urllib.request,
                "urlopen",
                side_effect=AssertionError("network requested for cached cover"),
            ):
                hero, size = module.download(url, key)

        self.assertEqual(hero, f"{module.IMG_PREFIX}/{name}")
        self.assertEqual(size, len(b"cached image"))

    def test_fetch_covers_replaces_an_empty_cached_file(self):
        module = load_script("fetch-covers.py")
        url = "https://example.com/cover.jpg"
        key = "page-id-and-cover-reference"
        response = unittest.mock.MagicMock()
        response.read.return_value = b"fresh image"

        with tempfile.TemporaryDirectory() as directory:
            module.OUT_IMG = directory
            name = module.hashlib.md5(key.encode()).hexdigest()[:12] + ".jpg"
            cached = Path(directory) / name
            cached.touch()

            with patch.object(module.urllib.request, "urlopen", return_value=response):
                hero, size = module.download(url, key)

            self.assertEqual(cached.read_bytes(), b"fresh image")

        self.assertEqual(hero, f"{module.IMG_PREFIX}/{name}")
        self.assertEqual(size, len(b"fresh image"))

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
