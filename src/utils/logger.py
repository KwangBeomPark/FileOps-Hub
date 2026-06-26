import logging
import os
import sys
from datetime import datetime

_logger_initialized = False


def _configure_console_encoding(stream):
    if hasattr(stream, "reconfigure"):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def setup_logger(log_level=logging.INFO):
    """
    애플리케이션 전역 로깅 설정을 초기화합니다.
    - 콘솔 출력(StreamHandler)
    - AppData/Local/IntegratedDataTool/logs/sync_YYYYMMDD.log 파일 출력
    """
    global _logger_initialized
    if _logger_initialized:
        return logging.getLogger()

    # AppData/Local 경로 획득
    local_app_data = os.environ.get('LOCALAPPDATA')
    if not local_app_data:
        # Fallback to user profile or current dir if LOCALAPPDATA is missing
        user_profile = os.environ.get('USERPROFILE')
        if user_profile:
            local_app_data = os.path.join(user_profile, 'AppData', 'Local')
        else:
            local_app_data = os.getcwd()

    log_dir = os.path.join(local_app_data, 'IntegratedDataTool', 'logs')
    try:
        os.makedirs(log_dir, exist_ok=True)
    except Exception:
        # 권한 오류 등으로 디렉토리 생성이 실패할 경우 현재 작업 디렉토리에 로그 디렉토리 생성
        log_dir = os.path.join(os.getcwd(), 'logs')
        os.makedirs(log_dir, exist_ok=True)

    today = datetime.now().strftime('%Y%m%d')
    log_file_path = os.path.join(log_dir, f'sync_{today}.log')

    # 루트 로거 획득
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # 포매터 정의
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 1. 콘솔 핸들러 추가
    _configure_console_encoding(sys.stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 2. 파일 핸들러 추가
    try:
        file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Failed to initialize file logger: {e}", file=sys.stderr)

    _logger_initialized = True
    
    logger.info(f"Logger initialized. Log file path: {log_file_path}")
    return logger

def get_logger():
    """초기화된 전역 로거를 가져옵니다. 없을 경우 기본 초기화합니다."""
    logger = logging.getLogger()
    if not logger.handlers:
        return setup_logger()
    return logger

def add_gui_handler(handler):
    """
    GUI 레이어에서 텍스트 위젯 등으로 로그를 수신할 수 있도록 커스텀 핸들러를 추가합니다.
    이 함수를 통해 Core 로직이 PyQt6 모듈을 직접 import하지 않는 구조를 유지합니다.
    """
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.info("GUI Logger Handler has been registered successfully.")
