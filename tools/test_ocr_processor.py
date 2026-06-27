import unittest
from unittest.mock import patch

from src.core.ocr_processor import OCRProcessor


class FakeConfig:
    def get(self, key, default=""):
        if key == "promotion_regex":
            return r"PL-[A-Z]TS[A-Z]-202\d{5}-\d{4}"
        return default

    def set(self, _key, _value):
        return True


class OCRProcessorTests(unittest.TestCase):
    def test_tesseract_failure_falls_back_to_windows_ocr(self):
        processor = OCRProcessor(FakeConfig())
        with (
            patch.object(processor, "check_tesseract_installed", return_value=True),
            patch("src.core.ocr_processor.Image.open", side_effect=RuntimeError("tess failed")),
            patch("src.core.ocr_processor.extract_text_with_windows_ocr", return_value="PL-ATSZ-20261234-6789"),
        ):
            success, promo_num, text, error = processor.process_image("sample.png")

        self.assertTrue(success)
        self.assertEqual(promo_num, "PL-ATSZ-20261234-6789")
        self.assertIn("PL-ATSZ", text)
        self.assertIsNone(error)

    def test_ocr_available_when_windows_fallback_exists(self):
        processor = OCRProcessor(FakeConfig())
        with (
            patch.object(processor, "check_tesseract_installed", return_value=False),
            patch.object(processor, "check_windows_ocr_available", return_value=True),
        ):
            self.assertTrue(processor.check_ocr_available())


if __name__ == "__main__":
    unittest.main()
