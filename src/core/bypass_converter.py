import os
import zipfile
import ctypes
from ctypes import wintypes
import logging

logger = logging.getLogger(__name__)

# Windows API constants for SetFileTime
KERNEL32 = ctypes.windll.kernel32 if hasattr(ctypes, 'windll') else None
GENERIC_WRITE = 0x40000000
OPEN_EXISTING = 3
FILE_WRITE_ATTRIBUTES = 0x0100
INVALID_HANDLE_VALUE = -1

def set_file_timestamps_windows(file_path, creation_time, access_time, modification_time):
    """
    Windows OS 레벨에서 파일의 생성 시간(Creation Time), 마지막 접근 시간(Access Time), 
    마지막 수정 시간(Modification Time)을 지정된 값(epoch float)으로 강밀 복구 설정합니다.
    """
    if not KERNEL32:
        # Windows가 아닌 환경에서는 os.utime으로 수정/액세스만 설정
        os.utime(file_path, (access_time, modification_time))
        return False
        
    def get_filetime(epoch_time):
        # Epoch(1970년 1월 1일)과 Windows FILETIME Epoch(1601년 1월 1일) 차이 보정
        # FILETIME은 100나노초 단위의 정수 값
        val = int((epoch_time + 11644473600) * 10000000)
        low = val & 0xFFFFFFFF
        high = (val >> 32) & 0xFFFFFFFF
        return wintypes.FILETIME(low, high)

    ft_creation = get_filetime(creation_time)
    ft_access = get_filetime(access_time)
    ft_modification = get_filetime(modification_time)

    # 쓰기 특성 권한으로 파일 개방
    handle = KERNEL32.CreateFileW(
        os.path.abspath(file_path),
        FILE_WRITE_ATTRIBUTES,
        0, # sharing mode
        None,
        OPEN_EXISTING,
        0,
        None
    )

    if handle == INVALID_HANDLE_VALUE:
        err = ctypes.GetLastError()
        logger.error(f"Failed to open file handle to set timestamps ({file_path}), Error code: {err}")
        return False

    try:
        success = KERNEL32.SetFileTime(
            handle,
            ctypes.byref(ft_creation),
            ctypes.byref(ft_access),
            ctypes.byref(ft_modification)
        )
        if not success:
            err = ctypes.GetLastError()
            logger.error(f"SetFileTime failed for {file_path}, Error code: {err}")
            return False
        return True
    finally:
        KERNEL32.CloseHandle(handle)


class BypassConverter:
    """
    Office 파일(Excel, PowerPoint, Word) 및 PDF 파일을 
    보안 정책 우회용 포맷으로 변환하고 메타데이터를 유지하는 코어 비즈니스 엔진
    """
    
    def __init__(self):
        self._office_installed_cache = {}
        
    def is_file_locked(self, file_path):
        """파일이 다른 프로세스에 의해 단독으로 열려 있거나 잠겨 있는지 검사합니다."""
        if not os.path.exists(file_path):
            return False
        try:
            # 쓰기 모드로 오픈을 시도하여 파일 락 여부 점검
            # 이미 다른 곳에서 독점 열기 상태면 PermissionError 발생
            with open(file_path, 'r+'):
                pass
            return False
        except IOError:
            return True
            
    def check_office_installed(self, app_name):
        """특정 Office 프로그램(Excel.Application 등)의 COM 호출 가능 여부 검사"""
        if app_name in self._office_installed_cache:
            return self._office_installed_cache[app_name]
            
        import win32com.client
        import pythoncom
        
        pythoncom.CoInitialize()
        try:
            app = win32com.client.DispatchEx(app_name)
            app.Quit()
            self._office_installed_cache[app_name] = True
            return True
        except Exception as e:
            logger.warning(f"{app_name} is not available/installed: {e}")
            self._office_installed_cache[app_name] = False
            return False
        finally:
            pythoncom.CoUninitialize()

    def convert_file(self, src_path, tgt_path, target_ext, preserve_meta=True, delete_original=True):
        """
        단일 파일을 변환하고, 메타데이터 보존 및 원본 삭제 처리를 수행합니다.
        
        Returns:
            tuple: (success, message)
        """
        src_path = os.path.normpath(src_path)
        tgt_path = os.path.normpath(tgt_path)
        
        if not os.path.exists(src_path):
            return False, f"원본 파일을 찾을 수 없습니다: {src_path}"
            
        if self.is_file_locked(src_path):
            return False, f"파일이 이미 다른 프로그램에서 사용 중입니다 (Locked): {os.path.basename(src_path)}"
            
        # 메타데이터 미리 백업
        stat = os.stat(src_path)
        creation_time = stat.st_ctime
        modification_time = stat.st_mtime
        access_time = stat.st_atime
        
        _, src_ext = os.path.splitext(src_path.lower())
        target_ext = target_ext.lower()
        
        # 대상 폴더 생성
        os.makedirs(os.path.dirname(tgt_path), exist_ok=True)
        
        success = False
        err_msg = ""
        
        # 1. 파일 유형별 알맞은 변환 실행
        try:
            if src_ext in ('.xlsx', '.xls', '.xlsm'):
                success, err_msg = self._convert_excel(src_path, tgt_path, target_ext)
            elif src_ext in ('.pptx', '.ppt', '.pptm'):
                success, err_msg = self._convert_powerpoint(src_path, tgt_path, target_ext)
            elif src_ext in ('.docx', '.doc', '.docm'):
                success, err_msg = self._convert_word(src_path, tgt_path, target_ext)
            elif src_ext == '.pdf':
                success, err_msg = self._convert_pdf(src_path, tgt_path, target_ext)
            else:
                success, err_msg = False, f"지원하지 않는 원본 파일 형식입니다: {src_ext}"
        except Exception as ex:
            success = False
            err_msg = f"변환 실패 (알 수 없는 오류): {str(ex)}"
            logger.exception("Exception in convert_file")
            
        if not success:
            return False, err_msg
            
        # 2. 메타데이터 (시간 타임스탬프) 복구 적용
        if preserve_meta and os.path.exists(tgt_path):
            try:
                set_file_timestamps_windows(tgt_path, creation_time, access_time, modification_time)
            except Exception as meta_ex:
                logger.error(f"Failed to restore metadata for {tgt_path}: {meta_ex}")
                # 메타데이터 보존 실패는 파일 자체의 변환 성공을 무효화하지는 않음 (경고만 기록)
                
        # 3. 원본 파일 안전 삭제
        if delete_original and success:
            try:
                # 읽기전용 속성 해제 후 삭제
                os.chmod(src_path, 0o777)
                os.remove(src_path)
            except Exception as del_ex:
                logger.error(f"Failed to delete original file {src_path}: {del_ex}")
                return True, f"변환 성공했으나 원본 파일 삭제 실패: {str(del_ex)}"
                
        return True, "성공"

    def _convert_excel(self, src_path, tgt_path, target_ext):
        """Excel COM 자동화를 이용한 바이너리/매크로 형식 변환"""
        if not self.check_office_installed("Excel.Application"):
            return False, "Microsoft Excel이 이 컴퓨터에 설치되어 있지 않거나 COM 실행이 불가능합니다."
            
        import win32com.client
        import pythoncom
        
        # Excel 파일 형식 매핑
        # xlExcel12 = 50 (.xlsb)
        # xlOpenXMLWorkbook = 51 (.xlsx)
        # xlOpenXMLWorkbookMacroEnabled = 52 (.xlsm)
        # xlExcel8 = 56 (.xls)
        fmt_map = {
            ".xlsb": 50,
            ".xlsx": 51,
            ".xlsm": 52,
            ".xls": 56
        }
        file_format = fmt_map.get(target_ext, 50)
        
        pythoncom.CoInitialize()
        excel = None
        wb = None
        try:
            excel = win32com.client.DispatchEx("Excel.Application")
            excel.DisplayAlerts = False
            excel.Visible = False
            
            wb = excel.Workbooks.Open(os.path.abspath(src_path))
            wb.SaveAs(os.path.abspath(tgt_path), FileFormat=file_format)
            wb.Close(SaveChanges=False)
            return True, "성공"
        except Exception as e:
            logger.error(f"Excel conversion failed: {e}")
            return False, f"Excel 변환 중 오류: {str(e)}"
        finally:
            try:
                if excel:
                    excel.Quit()
            except Exception:
                pass
            pythoncom.CoUninitialize()

    def _convert_powerpoint(self, src_path, tgt_path, target_ext):
        """PowerPoint COM 자동화를 이용한 매크로 활성화 형식 변환"""
        if not self.check_office_installed("PowerPoint.Application"):
            return False, "Microsoft PowerPoint가 이 컴퓨터에 설치되어 있지 않거나 COM 실행이 불가능합니다."
            
        import win32com.client
        import pythoncom
        
        # PPT 파일 형식 매핑
        # ppSaveAsOpenXMLPresentation = 24 (.pptx)
        # ppSaveAsOpenXMLPresentationMacroEnabled = 25 (.pptm)
        # ppSaveAsPresentation = 1 (.ppt)
        fmt_map = {
            ".pptx": 24,
            ".pptm": 25,
            ".ppt": 1
        }
        file_format = fmt_map.get(target_ext, 25)
        
        pythoncom.CoInitialize()
        powerpoint = None
        pres = None
        try:
            powerpoint = win32com.client.DispatchEx("PowerPoint.Application")
            
            # PowerPoint는 WithWindow=False로 열어야 백그라운드로 실행됨
            pres = powerpoint.Presentations.Open(os.path.abspath(src_path), WithWindow=False)
            pres.SaveAs(os.path.abspath(tgt_path), FileFormat=file_format)
            pres.Close()
            return True, "성공"
        except Exception as e:
            logger.error(f"PowerPoint conversion failed: {e}")
            return False, f"PowerPoint 변환 중 오류: {str(e)}"
        finally:
            try:
                if powerpoint:
                    powerpoint.Quit()
            except Exception:
                pass
            pythoncom.CoUninitialize()

    def _convert_word(self, src_path, tgt_path, target_ext):
        """Word COM 자동화를 이용한 매크로 활성화 형식 변환"""
        if not self.check_office_installed("Word.Application"):
            return False, "Microsoft Word가 이 컴퓨터에 설치되어 있지 않거나 COM 실행이 불가능합니다."
            
        import win32com.client
        import pythoncom
        
        # Word 파일 형식 매핑
        # wdFormatDocument = 0 (.doc)
        # wdFormatXMLDocument = 12 (.docx)
        # wdFormatXMLDocumentMacroEnabled = 13 (.docm)
        fmt_map = {
            ".docx": 12,
            ".docm": 13,
            ".doc": 0
        }
        file_format = fmt_map.get(target_ext, 13)
        
        pythoncom.CoInitialize()
        word = None
        doc = None
        try:
            word = win32com.client.DispatchEx("Word.Application")
            word.DisplayAlerts = 0
            word.Visible = False
            
            doc = word.Documents.Open(os.path.abspath(src_path))
            doc.SaveAs2(os.path.abspath(tgt_path), FileFormat=file_format)
            doc.Close(SaveChanges=False)
            return True, "성공"
        except Exception as e:
            logger.error(f"Word conversion failed: {e}")
            return False, f"Word 변환 중 오류: {str(e)}"
        finally:
            try:
                if word:
                    word.Quit()
            except Exception:
                pass
            pythoncom.CoUninitialize()

    def _convert_pdf(self, src_path, tgt_path, target_ext):
        """PDF 파일을 지정된 형식(ZIP 등)으로 변환"""
        if target_ext == '.zip':
            try:
                # PDF 파일을 ZIP 아카이브에 압축 포장
                with zipfile.ZipFile(tgt_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(src_path, arcname=os.path.basename(src_path))
                return True, "성공"
            except Exception as e:
                logger.error(f"PDF ZIP conversion failed: {e}")
                return False, f"PDF -> ZIP 압축 중 오류: {str(e)}"
        else:
            # 우회하지 않고 단순 복제 처리
            try:
                import shutil
                shutil.copy2(src_path, tgt_path)
                return True, "성공"
            except Exception as e:
                return False, f"PDF 복제 오류: {str(e)}"
