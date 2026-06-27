import os
import tempfile
import unittest
from unittest.mock import patch

from src.core.updater import AutoUpdater


class FakeResponse:
    def __init__(self, payload=b"", total_size=None, chunks=None):
        self.payload = payload
        self.total_size = total_size
        self.chunks = list(chunks or [])

    def __enter__(self):
        return self

    def __exit__(self, _exc_type, _exc, _tb):
        return False

    def read(self, _size=-1):
        if self.chunks:
            return self.chunks.pop(0)
        payload, self.payload = self.payload, b""
        return payload

    def info(self):
        size = self.total_size if self.total_size is not None else len(self.payload)
        return {"Content-Length": str(size)}


class FakeOpener:
    def __init__(self, response):
        self.response = response

    def open(self, _req, timeout=15):
        return self.response


class UpdaterTests(unittest.TestCase):
    def test_version_comparison(self):
        updater = AutoUpdater(current_version="v1.0.0")

        self.assertTrue(updater.is_newer_version("v1.0.0", "v1.0.1"))
        self.assertFalse(updater.is_newer_version("v1.0.1", "v1.0.1"))
        self.assertTrue(updater.is_newer_version("v20260625", "v20260626"))

    def test_download_rejects_non_https(self):
        updater = AutoUpdater()
        with tempfile.NamedTemporaryFile() as file:
            with self.assertRaises(ValueError):
                updater.download_file("http://github.com/example/setup.exe", file.name)

    def test_download_rejects_untrusted_domain(self):
        updater = AutoUpdater()
        with tempfile.NamedTemporaryFile() as file:
            with self.assertRaises(ValueError):
                updater.download_file("https://example.com/setup.exe", file.name)

    def test_release_asset_prefers_setup_exe(self):
        payload = (
            b'{"tag_name":"v1.0.1","body":"notes","assets":['
            b'{"name":"source.zip","browser_download_url":"https://github.com/a/source.zip"},'
            b'{"name":"IntegratedDataTool.exe","browser_download_url":"https://github.com/a/app.exe"},'
            b'{"name":"IntegratedDataTool_Setup_v9.9.9.exe","browser_download_url":"https://github.com/a/setup.exe"}'
            b"]}"
        )
        updater = AutoUpdater(current_version="v1.0.0")

        with patch("urllib.request.urlopen", return_value=FakeResponse(payload=payload)):
            has_update, latest, download_url, notes = updater.check_for_updates()

        self.assertTrue(has_update)
        self.assertEqual(latest, "v1.0.1")
        self.assertEqual(download_url, "https://github.com/a/setup.exe")
        self.assertEqual(notes, "notes")

    def test_update_check_records_error(self):
        updater = AutoUpdater(current_version="v1.1.2")

        with patch("urllib.request.urlopen", side_effect=OSError("network down")):
            has_update, latest, download_url, notes = updater.check_for_updates()

        self.assertFalse(has_update)
        self.assertEqual(latest, "v1.1.2")
        self.assertIsNone(download_url)
        self.assertEqual(notes, "")
        self.assertIn("network down", updater.last_error)

    def test_incomplete_download_is_deleted(self):
        updater = AutoUpdater()
        response = FakeResponse(total_size=10, chunks=[b"abc", b""])

        with tempfile.TemporaryDirectory() as tmpdir:
            dest_path = f"{tmpdir}\\download.exe"
            with patch("urllib.request.build_opener", return_value=FakeOpener(response)):
                with self.assertRaises(OSError):
                    updater.download_file("https://github.com/example/setup.exe", dest_path)

            self.assertFalse(os.path.exists(dest_path))


if __name__ == "__main__":
    unittest.main()
