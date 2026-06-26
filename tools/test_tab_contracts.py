import os
import tempfile
import unittest

from src.core.task_contracts import BypassRunConfig, PdfRunConfig, TaskValidationError
from src.ui.bypass_tab import BypassTab
from src.ui.pdf_tab import PDFTab


class TextValue:
    def __init__(self, value):
        self.value = value

    def text(self):
        return self.value


class CheckedValue:
    def __init__(self, value):
        self.value = value

    def isChecked(self):
        return self.value


class TableItem:
    def __init__(self, value):
        self.value = value

    def text(self):
        return self.value


class FakeTable:
    def __init__(self, rows):
        self.rows = rows

    def rowCount(self):
        return len(self.rows)

    def item(self, row, column):
        return TableItem(self.rows[row][column])


class TabContractTests(unittest.TestCase):
    def test_pdf_tab_builds_typed_config(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = os.path.join(temp_dir, "sample.pdf")
            output_dir = os.path.join(temp_dir, "out")
            with open(pdf_path, "wb") as file:
                file.write(b"%PDF-1.4\n")

            fake_tab = type("FakePDFTab", (), {})()
            fake_tab.selected_pdf_paths = [pdf_path]
            fake_tab.output_path_input = TextValue(output_dir)

            run_config = PDFTab.build_run_config(fake_tab)
            self.assertIsInstance(run_config, PdfRunConfig)
            self.assertEqual(run_config.pdf_paths, [pdf_path])
            self.assertEqual(run_config.output_folder, output_dir)

    def test_bypass_tab_requires_explicit_scan_before_integrated_run(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            fake_tab = self.make_bypass_fake(temp_dir, scanned_files=[], table_rows=[])

            with self.assertRaises(TaskValidationError):
                BypassTab.build_run_config(fake_tab)

    def test_bypass_tab_builds_config_from_current_scan_table(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source_path = os.path.join(temp_dir, "book.xlsx")
            with open(source_path, "wb") as file:
                file.write(b"x")

            fake_tab = self.make_bypass_fake(
                temp_dir,
                scanned_files=[source_path],
                table_rows=[["book.xlsx", "1.0 KB", ".xlsb", "대기 중"]],
            )

            run_config = BypassTab.build_run_config(fake_tab)
            self.assertIsInstance(run_config, BypassRunConfig)
            self.assertEqual(run_config.tasks[0].src, source_path)
            self.assertTrue(run_config.tasks[0].tgt.endswith(".xlsb"))

    def make_bypass_fake(self, source_dir, scanned_files, table_rows):
        fake_tab = type("FakeBypassTab", (), {})()
        fake_tab.src_entry = TextValue(source_dir)
        fake_tab.tgt_entry = TextValue("저장할 우회 폴더를 선택하세요.")
        fake_tab.scanned_files = scanned_files
        fake_tab.radio_inplace = CheckedValue(True)
        fake_tab.file_table = FakeTable(table_rows)
        fake_tab.check_preserve_meta = CheckedValue(True)
        fake_tab.check_delete_orig = CheckedValue(True)
        return fake_tab


if __name__ == "__main__":
    unittest.main()
