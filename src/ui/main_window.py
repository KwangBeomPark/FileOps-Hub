from PyQt6.QtWidgets import QMainWindow, QTabWidget, QMessageBox, QStatusBar
from PyQt6.QtGui import QAction
from PyQt6.QtCore import QThread, pyqtSignal

from src.ui.pdf_tab import PDFTab
from src.ui.ocr_tab import OCRTab
from src.ui.eml_tab import EMLTab
from src.ui.sync_tab import SyncTab
from src.ui.bypass_tab import BypassTab
from src.ui.task_tab import TaskTab
from src.ui.settings_dialog import SettingsDialog
from src.core.updater import AutoUpdater
from src.utils.config_manager import ConfigManager
from src.utils.logger import get_logger

logger = get_logger()

APP_STYLESHEET = """
QMainWindow, QDialog, QMessageBox, QInputDialog {
    background-color: #1e1e1e;
}
QTabWidget::pane {
    border: 1px solid #3e3e3e;
    background-color: #2d2d2d;
    top: -1px;
}
QTabBar::tab {
    background-color: #1e1e1e;
    color: #a0a0a0;
    padding: 10px 18px;
    border: 1px solid #3e3e3e;
    border-bottom: none;
    min-width: 130px;
}
QTabBar::tab:selected {
    background-color: #2d2d2d;
    color: #38bdf8;
    font-weight: bold;
}
QTabBar::tab:hover {
    background-color: #252526;
    color: #e2e8f0;
}
QGroupBox {
    border: 1px solid #3e3e3e;
    border-radius: 6px;
    margin-top: 15px;
    padding: 16px 10px 10px 10px;
    background-color: #252526;
    font-size: 10.5pt;
    font-weight: bold;
    color: #f1f5f9;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
    color: #38bdf8;
}
QLineEdit, QListWidget, QTextEdit, QTableWidget {
    border: 1px solid #3e3e3e;
    border-radius: 4px;
    background-color: #1e1e1e;
    color: #e2e8f0;
    padding: 5px;
    gridline-color: #2d2d2d;
}
QLineEdit:read-only {
    background-color: #252526;
    color: #8a949e;
}
QPushButton {
    border: 1px solid #3e3e3e;
    border-radius: 4px;
    background-color: #2d2d2d;
    color: #e2e8f0;
    padding: 7px 12px;
    min-height: 28px;
}
QPushButton:hover {
    background-color: #3e3e3e;
}
QPushButton:disabled {
    color: #64748b;
    background-color: #1e1e1e;
    border-color: #2d2d2d;
}
QPushButton[variant="primary"] {
    background-color: #0e639c;
    color: #ffffff;
    border-color: #1177bb;
    font-weight: bold;
}
QPushButton[variant="primary"]:hover {
    background-color: #1177bb;
}
QPushButton[variant="success"] {
    background-color: #16a34a;
    color: #ffffff;
    border-color: #15803d;
    font-weight: bold;
}
QPushButton[variant="success"]:hover {
    background-color: #15803d;
}
QPushButton[variant="danger"] {
    background-color: #b91c1c;
    color: #ffffff;
    border-color: #991b1b;
    font-weight: bold;
}
QPushButton[variant="danger"]:hover {
    background-color: #991b1b;
}
QProgressBar {
    border: 1px solid #3e3e3e;
    border-radius: 4px;
    background-color: #252526;
    height: 18px;
    text-align: center;
    color: #ffffff;
}
QProgressBar::chunk {
    border-radius: 3px;
    background-color: #0e639c;
}
QHeaderView::section {
    background-color: #252526;
    color: #e2e8f0;
    border: 1px solid #3e3e3e;
    padding: 6px;
    font-weight: bold;
}
QComboBox {
    background-color: #1e1e1e;
    color: #e2e8f0;
    border: 1px solid #3e3e3e;
    border-radius: 4px;
    padding: 5px 10px;
}
QComboBox QAbstractItemView {
    background-color: #1e1e1e;
    color: #e2e8f0;
    selection-background-color: #0e639c;
    selection-color: #ffffff;
    border: 1px solid #3e3e3e;
}
QLabel {
    color: #e2e8f0;
    font-size: 9.5pt;
}
QGroupBox QLabel {
    font-weight: bold;
    color: #cbd5e1;
}
QMenuBar {
    background-color: #1e1e1e;
    color: #e2e8f0;
    border-bottom: 1px solid #3e3e3e;
}
QMenuBar::item {
    background-color: transparent;
    padding: 5px 10px;
}
QMenuBar::item:selected {
    background-color: #2d2d2d;
}
QMenu {
    background-color: #1e1e1e;
    color: #e2e8f0;
    border: 1px solid #3e3e3e;
}
QMenu::item {
    padding: 5px 20px;
}
QMenu::item:selected {
    background-color: #0e639c;
    color: #ffffff;
}
QStatusBar {
    background-color: #1e1e1e;
    color: #a0a0a0;
    border-top: 1px solid #3e3e3e;
}
QScrollBar:vertical {
    background: #1e1e1e;
    width: 12px;
    margin: 0px;
    border: none;
}
QScrollBar::handle:vertical {
    background: #424242;
    min-height: 20px;
    border-radius: 6px;
}
QScrollBar::handle:vertical:hover {
    background: #4f4f4f;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    background: none;
    height: 0px;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}
QScrollBar:horizontal {
    background: #1e1e1e;
    height: 12px;
    margin: 0px;
    border: none;
}
QScrollBar::handle:horizontal {
    background: #424242;
    min-width: 20px;
    border-radius: 6px;
}
QScrollBar::handle:horizontal:hover {
    background: #4f4f4f;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    background: none;
    width: 0px;
}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: none;
}
QCheckBox {
    color: #cbd5e1;
}
"""


class UpdateWorker(QThread):
    finished = pyqtSignal(bool, str, str, str) # has_update, latest_version, download_url, release_notes
    
    def __init__(self, current_version="v1.0.0"):
        super().__init__()
        self.updater = AutoUpdater(current_version=current_version)
        
    def run(self):
        has_update, latest, url, notes = self.updater.check_for_updates()
        self.finished.emit(has_update, latest, url or "", notes)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.current_version = "v1.0.0" # 현재 애플리케이션 버전
        self.update_worker = None
        self.init_ui()
        
        # 저장소가 설정된 경우에만 시작 시 백그라운드 업데이트 확인
        if (
            self.config_manager.get("auto_check_update", "on_start") == "on_start"
            and self.config_manager.get("github_repo", "").strip()
        ):
            self.trigger_update_check(silent=True)
        
    def init_ui(self):
        self.setWindowTitle(f"Integrated Data & File Utility ({self.current_version})")
        self.setStyleSheet(APP_STYLESHEET)
        self.setMinimumSize(1000, 700)
        saved_size = self.config_manager.get("window_size", [1200, 800])
        if isinstance(saved_size, list) and len(saved_size) == 2:
            self.resize(int(saved_size[0]), int(saved_size[1]))
        else:
            self.resize(1200, 800)
        self.move(100, 100)
        
        # 탭 위젯 생성
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        self.setCentralWidget(self.tab_widget)
        
        # 각 탭 초기화 및 추가
        self.task_tab = TaskTab(self.config_manager)
        self.pdf_tab = PDFTab(self.config_manager)
        self.ocr_tab = OCRTab(self.config_manager)
        self.eml_tab = EMLTab(self.config_manager)
        self.sync_tab = SyncTab(self.config_manager)
        self.bypass_tab = BypassTab(self.config_manager)
        
        self.tab_widget.addTab(self.task_tab, "Task Runner")
        self.tab_widget.addTab(self.sync_tab, "Folder Sync")
        self.tab_widget.addTab(self.eml_tab, "EML Image")
        self.tab_widget.addTab(self.pdf_tab, "PDF Image")
        self.tab_widget.addTab(self.ocr_tab, "Image OCR")
        self.tab_widget.addTab(self.bypass_tab, "Bypass Convert")
        
        # 메뉴바 생성
        self.create_menu_bar()
        
        # 상태 표시줄
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
    def create_menu_bar(self):
        menu_bar = self.menuBar()
        
        # File 메뉴
        file_menu = menu_bar.addMenu("File")
        
        settings_action = QAction("Settings", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self.open_settings)
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Help 메뉴
        help_menu = menu_bar.addMenu("Help")
        
        check_update_action = QAction("Check for Updates...", self)
        check_update_action.triggered.connect(lambda: self.trigger_update_check(silent=False))
        help_menu.addAction(check_update_action)
        
    def trigger_update_check(self, silent=True):
        if self.update_worker and self.update_worker.isRunning():
            return

        if not self.config_manager.get("github_repo", "").strip():
            if not silent:
                QMessageBox.information(
                    self,
                    "업데이트 설정",
                    "Settings에서 GitHub 저장소(owner/repo)를 먼저 입력해 주세요."
                )
            return
            
        if not silent:
            self.status_bar.showMessage("Checking for updates...")
            
        self.update_worker = UpdateWorker(current_version=self.current_version)
        self.update_worker.finished.connect(lambda has_up, lat, url, notes: self.on_update_checked(has_up, lat, url, notes, silent))
        self.update_worker.start()
        
    def on_update_checked(self, has_update, latest_version, download_url, release_notes, silent):
        if not silent:
            self.status_bar.showMessage("Update check finished.", 3000)
            
        if has_update:
            msg = f"새로운 버전 ({latest_version})이 발견되었습니다!\n\n[릴리즈 노트]\n{release_notes}\n\n다운로드 페이지로 이동하시겠습니까?"
            reply = QMessageBox.question(
                self,
                "업데이트 알림",
                msg,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            if reply == QMessageBox.StandardButton.Yes:
                import webbrowser
                # 만약 자산 다운로드 URL이 있으면 그걸 열고, 없으면 릴리즈 전체 탭을 브라우저에 띄움
                target_url = download_url or "https://github.com/kwangbeom-park/Project06_py_DataOperting/releases"
                webbrowser.open(target_url)
        else:
            if not silent:
                QMessageBox.information(
                    self,
                    "업데이트 정보",
                    f"현재 최신 버전 ({self.current_version})을 사용하고 있습니다."
                )
                
    def open_settings(self):
        dialog = SettingsDialog(self.config_manager, self)
        if dialog.exec():
            self.ocr_tab.ocr_processor.setup_tesseract()
            logger.info("Settings updated and saved.")
            self.status_bar.showMessage("Settings saved successfully.", 3000)

    def set_all_tabs_locked(self, locked):
        """통합 태스크 실행 중 모든 탭 바 및 개별 탭 UI를 비활성화"""
        self.tab_widget.tabBar().setEnabled(not locked)
        self.sync_tab.set_ui_locked(locked)
        self.eml_tab.set_ui_locked(locked)
        self.pdf_tab.set_ui_locked(locked)
        self.ocr_tab.set_ui_locked(locked)
        self.bypass_tab.set_ui_locked(locked)

    def save_window_state(self):
        size = self.size()
        self.config_manager.set("window_size", [size.width(), size.height()])
            
    def closeEvent(self, event):
        active_tasks = []
        if self.task_tab.is_running:
            active_tasks.append("통합 일괄 실행")
        if self.pdf_tab.is_converting:
            active_tasks.append("PDF 이미지 변환")
        if self.ocr_tab.is_converting:
            active_tasks.append("이미지 OCR 이름 변경")
        if self.eml_tab.is_converting:
            active_tasks.append("EML 변환")
        if self.sync_tab.is_running:
            active_tasks.append("폴더 동기화")
        if self.bypass_tab.is_running:
            active_tasks.append("포맷 우회 변환")
            
        if active_tasks:
            task_list = ", ".join(active_tasks)
            reply = QMessageBox.question(
                self, 
                "작업 진행 중", 
                f"현재 [{task_list}] 작업이 실행 중입니다. 프로그램을 강제 종료하시겠습니까?\n(강제 종료 시 데이터 손상이 발생할 수 있습니다.)",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.task_tab.stop_all()
                self.pdf_tab.stop_all()
                self.ocr_tab.stop_all()
                self.eml_tab.stop_all()
                self.sync_tab.stop_all()
                self.bypass_tab.stop_all()
                self.save_window_state()
                event.accept()
            else:
                event.ignore()
        else:
            self.save_window_state()
            event.accept()
