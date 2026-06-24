import os
import time
import logging
import traceback
from PyQt6.QtCore import QThread, pyqtSignal

# Core Import
from src.core.sync_manager import SyncManager
from src.core.eml_converter import EMLConverter
from src.core.pdf_converter import PDFConverter
from src.core.ocr_processor import OCRProcessor
from src.core.bypass_converter import BypassConverter

logger = logging.getLogger(__name__)

class TaskWorker(QThread):
    # GUI 연결용 시그널 정의
    log_signal = pyqtSignal(str)                       # 로그 메세지
    step_progress = pyqtSignal(int, int, str)          # current_step_progress, total_step_files, detail_msg
    total_progress = pyqtSignal(int)                   # 0 ~ 100 (%)
    status_changed = pyqtSignal(str, str)              # tab_name, status_str
    finished = pyqtSignal(bool, str, str)              # is_success, message, report_body

    def __init__(self, config_manager, tasks_dict):
        """
        Args:
            config_manager: ConfigManager 인스턴스
            tasks_dict: 5개 탭의 설정 데이터 딕셔너리
                {
                    "sync": sync_data (또는 None),
                    "eml": eml_data (또는 None),
                    "pdf": pdf_data (또는 None),
                    "ocr": ocr_data (또는 None),
                    "bypass": bypass_data (또는 None)
                }
        """
        super().__init__()
        self.config_manager = config_manager
        self.tasks_dict = tasks_dict
        self.is_running = True
        
        # 각 탭의 실제 코어 인스턴스 생성
        self.eml_converter = EMLConverter(self.config_manager)
        self.pdf_converter = PDFConverter(self.config_manager)
        self.ocr_processor = OCRProcessor(self.config_manager)
        self.bypass_converter = BypassConverter()
        
    def stop(self):
        """작업 취소 요청"""
        self.is_running = False
        # EML 및 기타 모듈 취소 시그널 전달
        try:
            self.eml_converter.cancel()
        except Exception:
            pass

    def run(self):
        self.is_running = True
        self.eml_converter.is_cancelled = False
        
        # 활성화된 단계 식별
        active_steps = []
        step_names = {
            "sync": "Folder Sync",
            "eml": "EML Image",
            "pdf": "PDF Image",
            "ocr": "Image OCR",
            "bypass": "Bypass Convert"
        }
        
        for key in ["sync", "eml", "pdf", "ocr", "bypass"]:
            if self.tasks_dict.get(key) is not None:
                active_steps.append(key)
                
        total_steps = len(active_steps)
        if total_steps == 0:
            self.finished.emit(False, "실행할 활성 태스크가 없습니다. 각 탭의 세팅을 확인해 주세요.", "")
            return
            
        self.log_signal.emit("=" * 60)
        self.log_signal.emit("▶ 통합 일괄 순차 실행 작업을 시작합니다.")
        self.log_signal.emit(f"활성화된 작업 단계 ({total_steps}개): " + ", ".join([step_names[k] for k in active_steps]))
        self.log_signal.emit("=" * 60)
        
        # 리포트 작성을 위한 딕셔너리
        report_results = {k: {"status": "대기 중", "details": [], "success_count": 0, "total_count": 0} for k in active_steps}
        
        current_step_idx = 0
        self.total_progress.emit(0)
        
        # 1. Folder Sync
        if "sync" in active_steps:
            if not self._check_continue("sync"): return
            current_step_idx += 1
            self.status_changed.emit("sync", "진행 중")
            self.log_signal.emit("\n[1단계: Folder Sync 동기화 진행]")
            
            sync_data = self.tasks_dict["sync"]
            groups = sync_data.get("sync_groups", [])
            total_groups = len(groups)
            success_count = 0
            
            try:
                for idx, group in enumerate(groups):
                    if not self.is_running: break
                    self.log_signal.emit(f" -> 그룹 [{group['name']}] 동기화 분석 및 실행 중...")
                    self.step_progress.emit(idx, total_groups, f"그룹 동기화 진행 중: {group['name']}")
                    
                    folders = group.get("folders", [])
                    move_to_deleted = group.get("move_to_deleted", True)
                    
                    manager = SyncManager(folders=folders, move_to_deleted=move_to_deleted)
                    actions = manager.analyze_sync()
                    
                    # 동기화 실행
                    success_files, fail_files, errors = manager.execute_sync(actions)
                    
                    if len(errors) == 0:
                        success_count += 1
                        msg = f"✓ 그룹 [{group['name']}] 완료 (성공: {success_files}건, 실패: {fail_files}건)"
                        self.log_signal.emit(f"   {msg}")
                        report_results["sync"]["details"].append(msg)
                    else:
                        msg = f"⚠ 그룹 [{group['name']}] 일부 오류 발생 (성공: {success_files}건, 실패: {fail_files}건)"
                        self.log_signal.emit(f"   {msg}")
                        for err in errors[:5]:
                            self.log_signal.emit(f"     - 에러: {err}")
                        report_results["sync"]["details"].append(msg)
                        
                report_results["sync"]["success_count"] = success_count
                report_results["sync"]["total_count"] = total_groups
                report_results["sync"]["status"] = "완료" if success_count == total_groups else "일부 실패"
                self.status_changed.emit("sync", report_results["sync"]["status"])
                self.step_progress.emit(total_groups, total_groups, "Folder Sync 완료")
                
            except Exception as e:
                err_trace = traceback.format_exc()
                logger.error(f"Error in Sync step: {e}\n{err_trace}")
                self.log_signal.emit(f" ✗ Folder Sync 실패: {e}")
                report_results["sync"]["status"] = "실패"
                report_results["sync"]["details"].append(f"치명적 오류: {str(e)}")
                self.status_changed.emit("sync", "실패")
                
            self._update_total_progress(current_step_idx, total_steps)

        # 2. EML Image
        if "eml" in active_steps:
            if not self._check_continue("eml"): return
            current_step_idx += 1
            self.status_changed.emit("eml", "진행 중")
            self.log_signal.emit("\n[2단계: EML Image 파일 변환 진행]")
            
            eml_data = self.tasks_dict["eml"]
            tasks = eml_data.get("tasks", [])
            width = eml_data.get("width", 1024)
            total_tasks = len(tasks)
            success_tasks = 0
            
            try:
                for idx, task in enumerate(tasks):
                    if not self.is_running: break
                    self.log_signal.emit(f" -> 태스크 [{task['name']}] EML 파일 변환 시작...")
                    self.step_progress.emit(idx, total_tasks, f"EML 태스크 진행 중: {task['name']}")
                    
                    src = task.get("source_folder", "")
                    tgt = task.get("target_folder", "")
                    
                    os.makedirs(tgt, exist_ok=True)
                    eml_files = [os.path.join(src, f) for f in os.listdir(src) if f.lower().endswith('.eml')]
                    total_files = len(eml_files)
                    
                    if total_files == 0:
                        self.log_signal.emit(f"   ✗ 경고: '{task['name']}' 폴더 내에 EML 파일이 없습니다.")
                        report_results["eml"]["details"].append(f"태스크 [{task['name']}] EML 파일 없음 (건너뜀)")
                        continue
                        
                    task_success_count = 0
                    for file_idx, eml_path in enumerate(eml_files):
                        if not self.is_running: break
                        filename = os.path.basename(eml_path)
                        self.step_progress.emit(idx, total_tasks, f"EML 변환 중: {filename} ({file_idx+1}/{total_files})")
                        
                        out_png = os.path.join(tgt, os.path.splitext(filename)[0] + ".png")
                        try:
                            success = self.eml_converter.convert_eml_to_image(eml_path, out_png, width=width)
                            if success:
                                task_success_count += 1
                            else:
                                self.log_signal.emit(f"      ✗ 변환 실패: {filename}")
                        except Exception as file_err:
                            self.log_signal.emit(f"      ✗ 오류 발생 ({filename}): {file_err}")
                            
                    if not self.is_running: break
                    
                    if task_success_count == total_files:
                        success_tasks += 1
                        msg = f"✓ 태스크 [{task['name']}] 완료 (성공: {task_success_count}/{total_files})"
                        self.log_signal.emit(f"   {msg}")
                        report_results["eml"]["details"].append(msg)
                    else:
                        msg = f"⚠ 태스크 [{task['name']}] 일부 완료 (성공: {task_success_count}/{total_files})"
                        self.log_signal.emit(f"   {msg}")
                        report_results["eml"]["details"].append(msg)
                        
                report_results["eml"]["success_count"] = success_tasks
                report_results["eml"]["total_count"] = total_tasks
                report_results["eml"]["status"] = "완료" if success_tasks == total_tasks else "일부 실패"
                self.status_changed.emit("eml", report_results["eml"]["status"])
                self.step_progress.emit(total_tasks, total_tasks, "EML Image 변환 완료")
                
            except Exception as e:
                logger.error(f"Error in EML step: {e}")
                self.log_signal.emit(f" ✗ EML Image 변환 실패: {e}")
                report_results["eml"]["status"] = "실패"
                report_results["eml"]["details"].append(f"치명적 오류: {str(e)}")
                self.status_changed.emit("eml", "실패")
            finally:
                try:
                    self.eml_converter.cancel()
                except Exception:
                    pass
                    
            self._update_total_progress(current_step_idx, total_steps)

        # 3. PDF Image
        if "pdf" in active_steps:
            if not self._check_continue("pdf"): return
            current_step_idx += 1
            self.status_changed.emit("pdf", "진행 중")
            self.log_signal.emit("\n[3단계: PDF Image 변환 진행]")
            
            pdf_data = self.tasks_dict["pdf"]
            pdf_paths = pdf_data.get("pdf_paths", [])
            output_folder = pdf_data.get("output_folder", "")
            total_files = len(pdf_paths)
            success_count = 0
            
            try:
                os.makedirs(output_folder, exist_ok=True)
                for idx, pdf_path in enumerate(pdf_paths):
                    if not self.is_running: break
                    filename = os.path.basename(pdf_path)
                    self.log_signal.emit(f" -> PDF 변환 중: {filename}...")
                    self.step_progress.emit(idx, total_files, f"PDF 변환 진행 중: {filename}")
                    
                    try:
                        image_paths = self.pdf_converter.convert(pdf_path, output_folder)
                        success_count += 1
                        msg = f"✓ PDF [{filename}] 완료 -> 이미지 {len(image_paths)}개 생성"
                        self.log_signal.emit(f"   {msg}")
                        report_results["pdf"]["details"].append(msg)
                    except Exception as file_err:
                        msg = f"✗ PDF [{filename}] 변환 실패: {file_err}"
                        self.log_signal.emit(f"   {msg}")
                        report_results["pdf"]["details"].append(msg)
                        
                report_results["pdf"]["success_count"] = success_count
                report_results["pdf"]["total_count"] = total_files
                report_results["pdf"]["status"] = "완료" if success_count == total_files else "일부 실패"
                self.status_changed.emit("pdf", report_results["pdf"]["status"])
                self.step_progress.emit(total_files, total_files, "PDF Image 변환 완료")
                
            except Exception as e:
                logger.error(f"Error in PDF step: {e}")
                self.log_signal.emit(f" ✗ PDF Image 변환 실패: {e}")
                report_results["pdf"]["status"] = "실패"
                report_results["pdf"]["details"].append(f"치명적 오류: {str(e)}")
                self.status_changed.emit("pdf", "실패")
                
            self._update_total_progress(current_step_idx, total_steps)

        # 4. Image OCR
        if "ocr" in active_steps:
            if not self._check_continue("ocr"): return
            current_step_idx += 1
            self.status_changed.emit("ocr", "진행 중")
            self.log_signal.emit("\n[4단계: Image OCR 리네임 진행]")
            
            ocr_data = self.tasks_dict["ocr"]
            image_paths = ocr_data.get("image_paths", [])
            total_files = len(image_paths)
            success_count = 0
            
            try:
                for idx, img_path in enumerate(image_paths):
                    if not self.is_running: break
                    filename = os.path.basename(img_path)
                    self.log_signal.emit(f" -> OCR 분석 중: {filename}...")
                    self.step_progress.emit(idx, total_files, f"OCR 진행 중: {filename}")
                    
                    try:
                        success, promo_num, ocr_text, error_msg = self.ocr_processor.process_image(img_path)
                        
                        if success and promo_num:
                            ext = os.path.splitext(filename)[1]
                            dir_path = os.path.dirname(img_path)
                            new_name = f"{promo_num}{ext}"
                            target_path = os.path.join(dir_path, new_name)
                            
                            # 충돌방지
                            if os.path.exists(target_path) and target_path != img_path:
                                counter = 1
                                while True:
                                    new_name = f"{promo_num}_{counter}{ext}"
                                    target_path = os.path.join(dir_path, new_name)
                                    if not os.path.exists(target_path):
                                        break
                                    counter += 1
                                    
                            if target_path != img_path:
                                if os.path.exists(target_path):
                                    os.chmod(target_path, 0o777)
                                    os.remove(target_path)
                                os.chmod(img_path, 0o777)
                                os.rename(img_path, target_path)
                                final_filename = os.path.basename(target_path)
                            else:
                                final_filename = filename
                                
                            success_count += 1
                            msg = f"✓ OCR 성공: {filename} -> {final_filename} (프로모션: {promo_num})"
                            self.log_signal.emit(f"   {msg}")
                            report_results["ocr"]["details"].append(msg)
                        else:
                            msg = f"✗ OCR 분석 실패 (프로모션 미발견): {filename} ({error_msg or '미인식'})"
                            self.log_signal.emit(f"   {msg}")
                            report_results["ocr"]["details"].append(msg)
                            
                    except Exception as file_err:
                        msg = f"✗ OCR 파일 분석 오류 ({filename}): {file_err}"
                        self.log_signal.emit(f"   {msg}")
                        report_results["ocr"]["details"].append(msg)
                        
                report_results["ocr"]["success_count"] = success_count
                report_results["ocr"]["total_count"] = total_files
                report_results["ocr"]["status"] = "완료" if success_count == total_files else "일부 실패"
                self.status_changed.emit("ocr", report_results["ocr"]["status"])
                self.step_progress.emit(total_files, total_files, "Image OCR 완료")
                
            except Exception as e:
                logger.error(f"Error in OCR step: {e}")
                self.log_signal.emit(f" ✗ Image OCR 실패: {e}")
                report_results["ocr"]["status"] = "실패"
                report_results["ocr"]["details"].append(f"치명적 오류: {str(e)}")
                self.status_changed.emit("ocr", "실패")
                
            self._update_total_progress(current_step_idx, total_steps)

        # 5. Bypass Convert
        if "bypass" in active_steps:
            if not self._check_continue("bypass"): return
            current_step_idx += 1
            self.status_changed.emit("bypass", "진행 중")
            self.log_signal.emit("\n[5단계: Bypass Convert 우회 변환 진행]")
            
            bypass_data = self.tasks_dict["bypass"]
            tasks = bypass_data.get("tasks", [])
            delete_original = bypass_data.get("delete_original", True)
            total_files = len(tasks)
            success_count = 0
            
            # COM 컴포넌트 호출 안전 확보
            import pythoncom
            pythoncom.CoInitialize()
            
            try:
                for idx, task in enumerate(tasks):
                    if not self.is_running: break
                    src = task["src"]
                    tgt = task["tgt"]
                    ext = task["ext"]
                    preserve_meta = task["preserve_meta"]
                    
                    filename = os.path.basename(src)
                    self.log_signal.emit(f" -> 우회 변환 중: {filename} -> {ext}...")
                    self.step_progress.emit(idx, total_files, f"우회 변환 진행 중: {filename}")
                    
                    try:
                        success, msg = self.bypass_converter.convert_file(
                            src_path=src,
                            tgt_path=tgt,
                            target_ext=ext,
                            preserve_meta=preserve_meta,
                            delete_original=delete_original
                        )
                        
                        if success:
                            success_count += 1
                            rep_msg = f"✓ 우회 완료: {filename} -> {os.path.basename(tgt)}"
                            self.log_signal.emit(f"   {rep_msg}")
                            report_results["bypass"]["details"].append(rep_msg)
                        else:
                            rep_msg = f"✗ 우회 실패 ({filename}): {msg}"
                            self.log_signal.emit(f"   {rep_msg}")
                            report_results["bypass"]["details"].append(rep_msg)
                            
                    except Exception as file_err:
                        rep_msg = f"✗ 우회 파일 변환 오류 ({filename}): {file_err}"
                        self.log_signal.emit(f"   {rep_msg}")
                        report_results["bypass"]["details"].append(rep_msg)
                        
                report_results["bypass"]["success_count"] = success_count
                report_results["bypass"]["total_count"] = total_files
                report_results["bypass"]["status"] = "완료" if success_count == total_files else "일부 실패"
                self.status_changed.emit("bypass", report_results["bypass"]["status"])
                self.step_progress.emit(total_files, total_files, "Bypass Convert 완료")
                
            except Exception as e:
                logger.error(f"Error in Bypass step: {e}")
                self.log_signal.emit(f" ✗ Bypass Convert 실패: {e}")
                report_results["bypass"]["status"] = "실패"
                report_results["bypass"]["details"].append(f"치명적 오류: {str(e)}")
                self.status_changed.emit("bypass", "실패")
            finally:
                pythoncom.CoUninitialize()
                
            self._update_total_progress(current_step_idx, total_steps)
            
        # 6. 최종 결과 요약 및 이메일 리포트 작성
        self.total_progress.emit(100)
        
        if not self.is_running:
            self.finished.emit(False, "사용자에 의해 전체 작업이 중지되었습니다.", "")
            return
            
        # 리포트 본문 작성 (HTML 호환 및 텍스트 듀얼 가능 마크다운)
        report_lines = []
        report_lines.append("# 통합 태스크 실행 결과 보고서")
        report_lines.append(f"- **실행 일시**: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        report_lines.append("## [1] 작업 단계별 상태 요약")
        
        summary_table = [
            "| 작업 단계 | 상태 | 성공 개수 / 전체 개수 |",
            "| :--- | :--- | :--- |"
        ]
        for key in active_steps:
            status = report_results[key]["status"]
            success = report_results[key]["success_count"]
            total = report_results[key]["total_count"]
            summary_table.append(f"| {step_names[key]} | {status} | {success} / {total} |")
            
        report_lines.extend(summary_table)
        report_lines.append("")
        report_lines.append("## [2] 세부 변동 내역")
        
        for key in active_steps:
            report_lines.append(f"### 📍 {step_names[key]} 상세 내역")
            details = report_results[key]["details"]
            if details:
                for line in details:
                    report_lines.append(f"- {line}")
            else:
                report_lines.append("- 실행된 세부 변동 사항이 없습니다.")
            report_lines.append("")
            
        report_body = "\n".join(report_lines)
        
        self.log_signal.emit("\n" + "=" * 60)
        self.log_signal.emit("🎉 모든 통합 순차 실행이 완료되었습니다!")
        self.log_signal.emit("=" * 60)
        
        overall_success = all(
            report_results[key]["status"] == "완료" for key in active_steps
        )
        if overall_success:
            message = "통합 태스크 실행이 완료되었습니다."
        else:
            message = "통합 태스크 실행은 끝났지만 일부 작업이 실패했습니다. 결과 보고서를 확인해 주세요."

        self.finished.emit(overall_success, message, report_body)

    def _check_continue(self, step_key) -> bool:
        if not self.is_running:
            self.status_changed.emit(step_key, "취소됨")
            self.finished.emit(False, "작업 중지됨", "")
            return False
        return True

    def _update_total_progress(self, current_step, total_steps):
        percent = int((current_step / total_steps) * 100)
        self.total_progress.emit(percent)
