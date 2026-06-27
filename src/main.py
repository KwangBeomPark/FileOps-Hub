import sys
import os

# 프로젝트 루트 경로 및 src 경로를 sys.path에 추가하여 외부 모듈 탐색 보장
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_path = os.path.join(PROJECT_ROOT, "src")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from PyQt6.QtWidgets import QApplication
from src.ui.main_window import MainWindow, APP_STYLESHEET, create_dark_palette
from src.utils.logger import setup_logger

def main():
    # 로그 시스템 초기화
    setup_logger()
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setPalette(create_dark_palette())
    app.setStyleSheet(APP_STYLESHEET)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
