import pytesseract
from PIL import Image
import re
import os

class OCRProcessor:
    """이미지에서 텍스트를 추출하고 프로모션 번호를 찾는 클래스"""
    
    def __init__(self, config_manager):
        """
        Args:
            config_manager: ConfigManager 인스턴스
        """
        self.config_manager = config_manager
        self.setup_tesseract()
        
    def setup_tesseract(self):
        """Tesseract 경로 설정"""
        tesseract_path = self.config_manager.get('tesseract_path', '')
        
        if tesseract_path and os.path.exists(tesseract_path):
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        else:
            # 기본 경로 시도 (Windows)
            default_paths = [
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            ]
            
            for path in default_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    # 설정에 저장
                    self.config_manager.set('tesseract_path', path)
                    break
    
    def check_tesseract_installed(self):
        """Tesseract 설치 여부 확인
        
        Returns:
            bool: 설치되어 있으면 True
        """
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False
    
    def extract_text(self, image_path):
        """이미지에서 텍스트 추출
        
        Args:
            image_path: 이미지 파일 경로
            
        Returns:
            str: 추출된 텍스트
            
        Raises:
            Exception: OCR 실패 시
        """
        try:
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image, lang='eng')
            return text.strip()
        except Exception as e:
            raise Exception(f"OCR 텍스트 추출 실패: {str(e)}") from e
    
    def find_promotion_number(self, text):
        """텍스트에서 프로모션 번호 찾기
        
        Args:
            text: 검색할 텍스트
            
        Returns:
            str or None: 찾은 프로모션 번호, 없으면 None
        """
        pattern = self.config_manager.get('promotion_regex', r'PL-[A-Z]TS[A-Z]-202\d{5}-\d{4}')
        try:
            match = re.search(pattern, text)
        except re.error as e:
            # 설정된 정규식이 잘못되었을 경우 에러 로깅 후 기본 정규식으로 폴백
            from src.utils.logger import get_logger
            get_logger().error(f"Invalid regex pattern '{pattern}' in configuration: {e}. Falling back to default pattern.")
            default_pattern = r'PL-[A-Z]TS[A-Z]-202\d{5}-\d{4}'
            try:
                match = re.search(default_pattern, text)
            except re.error:
                match = None
                
        if match:
            return match.group(0)
        else:
            return None
    
    def process_image(self, image_path):
        """이미지 처리: 텍스트 추출 + 프로모션 번호 찾기
        
        Args:
            image_path: 이미지 파일 경로
            
        Returns:
            tuple: (success, promotion_number, extracted_text, error_message)
        """
        try:
            text = self.extract_text(image_path)
            promotion_number = self.find_promotion_number(text)
            
            if promotion_number:
                return (True, promotion_number, text, None)
            else:
                return (False, None, text, "프로모션 번호를 찾을 수 없습니다")
        except Exception as e:
            return (False, None, "", str(e))
