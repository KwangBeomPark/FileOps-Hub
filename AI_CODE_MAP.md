# AI_CODE_MAP.md - 프로젝트 전용 코드 지도

본 문서는 현재 프로젝트인 '통합 데이터 처리 및 파일 관리 도구 (Data Operating Tool)'의 목적, 기술 스택, 핵심 구조와 특수 주의사항을 관리하는 단일 진실 공급원(Single Source of Truth)입니다.

## 1. 프로젝트 목적 및 실행 환경
- **최신 목적**:
  - 회사 내 유관부서가 각자 관리하는 최신 팀 매뉴얼과 자료를 영업, 매니지먼트, 부서 리더가 사용하는 공용 배포 폴더와 연결하는 **통합 파일 운영 허브**입니다.
  - 여러 팀 폴더와 공용 폴더를 대등하게 비교하는 양방향 최신본 동기화, 구버전·충돌본 보존, 저장소 호환 포맷 변환을 한 애플리케이션에서 관리합니다.
  - 프로모션 정산·크로스 체크의 원천인 PDF/EML을 이미지로 만들고 OCR로 프로모션 번호와 텍스트를 판독할 수 있도록 전처리합니다.
  - 위 작업을 순차 또는 매일 지정 시각에 실행하고 성공·부분 실패 보고서를 설정된 담당자/활용 팀 이메일로 전송합니다. 메일 실패 시 로컬 보고서를 보존합니다.
- **권한 경계**:
  - 애플리케이션이 사용자나 팀 권한을 직접 생성·부여하지는 않습니다.
  - Windows 네트워크 드라이브, OneDrive, SharePoint에서 설정한 기존 ACL과 현재 로그인 사용자의 권한을 사용해 허용된 폴더만 처리합니다.
- **현재 구현 경계**:
  - 예약 실행은 애플리케이션이 실행 중일 때 동작하며 Windows 서비스가 아닙니다.
  - 동기화는 각 등록 폴더의 최상위 파일만 처리합니다. 하위 폴더 재귀 동기화는 구현되어 있지 않습니다.
  - EML 폴더 작업은 설정에 영속화되지만 PDF/OCR은 현재 GUI에서 선택한 파일을 대상으로 합니다.
- **기술 스택**:
  - Python 3.14+ / PyQt6 (GUI 프레임워크)
  - PyMuPDF (PDF 처리)
  - Playwright (EML HTML 렌더링 및 캡처)
  - PyInstaller (단일 실행 파일 빌드)
  - win32com.client / pythoncom (Office Automation)

## 2. 핵심 폴더 구조 및 주요 파일 역할
- `c:/Users/kwangbeom.park/Documents/Project06_py_DataOperting` (루트)
  - `myAGENT.md`: 공통 개발 원칙 및 검증 파이프라인 지침
  - `AI_CODE_MAP.md`: 프로젝트 전용 코드 지도 (본 파일)
  - `README.md`: 사용자 관점 목적, 설치, 실행, 운영 경계
  - `task.md`: 현재 감사·수정 단계 체크리스트
  - `walkthrough.md`: 전수 점검 결과와 남은 수동 검증
  - `IntegratedDataTool.spec`: PyInstaller 패키징 스펙 파일
  - `requirements.txt`: 통합 프로젝트 외부 의존성 목록
  - `src/` (통합 프로그램 소스코드 폴더)
    - `main.py`: 통합 GUI 프로그램의 진입점 (QApplication)
    - `core/`
      - `pdf_converter.py`: PDF 파일 내의 페이지를 이미지로 변환 및 추출하는 렌더링 모듈 (OCR 기능은 ocr_processor.py로 완전히 분리됨)
      - `eml_converter.py`: EML 파일 HTML 파싱 및 Playwright 연동 캡처 엔진
      - `sync_manager.py`: 다중 폴더 동기화 버전 분석 및 실행 엔진
      - `updater.py`: GitHub Releases API 연동 최신 버전 확인 엔진
      - `bypass_converter.py`: Office(Excel/Word/PPT) COM 자동화 및 PDF -> ZIP 압축 우회 변환, Windows 파일 타임스탬프(ctime/mtime/atime) 복원 보존 엔진
      - `email_sender.py`: SMTP 서버 연동(SSL/TLS STARTTLS 자동 지원) 및 DPAPI 비밀번호 복호화 기반 결과 리포트 메일 송부 모듈 (신규 추가)
      - `task_engine.py`: 5개 개별 탭의 코어를 동적/비동기 연계하여 순차 실행 및 리포트 작성 총괄 엔진 (신규 추가)
      - `ocr_processor.py`: Tesseract OCR 엔진 연동 및 비동기 OCR 텍스트 추출/파일명 추천 처리 모듈 (신규 추가)
      - `file_manager.py`: 파일 복사, 이동 및 중복 처리 방지를 포함한 파일 I/O 관련 헬퍼 모듈 (신규 추가)
    - `ui/`
      - `main_window.py`: 메인 윈도우 인터페이스, 메뉴바, 백그라운드 스레드 제어
      - `pdf_tab.py`: PDF Drop Zone 및 순수 이미지 변환 인터페이스 (OCR 기능 제거됨)
      - `ocr_tab.py`: 임의 이미지 다중 파일 추가, 체크박스 선택 제어 및 비동기 OCR 리네임 인터페이스
      - `eml_tab.py`: 다중 EML 변환 태스크 관리 및 배치 이미지 일괄 변환 인터페이스
      - `eml_task_dialog.py`: EML 태스크(소스/대상 폴더 및 이름) 개별 추가/수정용 입력창 다이얼로그
      - `sync_tab.py`: 다중 동기화 그룹 관리 및 전체 일괄 동기화(Sync ALL) 분석/실행 그리드 테이블 인터페이스
      - `settings_dialog.py`: SMTP 이메일 서버/발신자/수신자 및 DPAPI 암호화 패스워드 설정, GitHub Access Token, Tesseract.exe 경로 저장 다이얼로그
      - `toast_notification.py`: 세련된 슬라이드형 팝업 토스트 알림 컴포넌트
      - `image_preview_dialog.py`: OCR 리네임 전 원본 이미지 확대 미리보기 컴포넌트
      - `bypass_tab.py`: 소스/대상 경로 선택(Drag & Drop 지원), 타겟 확장자 지정, 변환 목록 시뮬레이션(Dry Run) 및 백그라운드 변환 실행 UI
      - `task_tab.py`: 5개 탭 일괄 순차 실행 통제, 앱 실행 중 일일 예약 실행, 진행 상태 그리드, 결과 메일 전송/로컬 Fallback UI. 예약 로직은 `check_scheduled_run()`(약 248행), 실행 수집은 `start_all_tasks()`(약 274행), 결과 통지는 `on_tasks_finished()`(약 411행)
      - `workflow_widget.py`: PDF 변환 및 파일 이동 등 전체 5개 단계 워크플로우 진행 상태를 시각화하는 인디케이터 위젯 (신규 추가)
    - `utils/`
      - `config_manager.py`: JSON 설정 파일 관리 및 암복호화 스레드 안전 호출 인터페이스
      - `security.py`: ctypes 경유 Windows DPAPI 호출을 통한 보안 인증 정보 저장 모듈
      - `logger.py`: AppData/Local 로그 로테이션 설정 모듈
  - `tools/` (자가 검증 테스트 폴더)
    - `test_security.py`: Windows DPAPI 암복호화 및 ConfigManager 스레드 안전성 검증
    - `test_sync.py`: 파일 버전 파싱, 경로 탈출 보안 방어 및 다중 폴더 동기화 매칭 검증
    - `test_eml.py`: EML HTML 본문 추출 및 Playwright 브라우저 헤드리스 이미지 렌더링 검증
    - `test_ocr_tab.py`: 가상 이미지 리스트 대상 OCRWorker 실행 및 이름 충돌 방지 검증
    - `test_robustness.py`: 설정 파일 오염 시 자동 복원, 정규식 오류 방어, Playwright 오프라인 연속 설치 루프 캐시 차단 검증
    - `test_gui_connections.py`: PyQt6 탭 위젯 로드 구조 및 비동기 스레드 상태 닫기 이벤트 검증
    - `test_updater.py`: GitHub Release API 모킹 버전 계산 및 토큰 적재 검증
    - `test_integration.py`: 전체 모듈 연계 정상성 종합 흐름 검증
    - `test_bypass_tab.py`: 우회 변환 코어, Windows 파일 날짜 복원력, 파일 잠김 및 COM 모킹 변환 흐름 단위 테스트
    - `test_email_sender.py`: SMTP 전송 프로토콜(SSL/TLS) 및 에러 상태 모킹 단위 테스트 (신규 추가)
    - `test_task_engine.py`: 통합 일괄 순차 실행 루프 및 최종 리포트 마크다운 가공 단위 테스트 (신규 추가)
    - `test_eml_tasks.py`: EML 다중 작업 비동기 처리(EMLWorker) 및 특정 에러 발생 시 격리성(Error Isolation) 검증 (신규 추가)
    - `test_pdf_converter.py`: 실제 임시 PDF의 페이지 수 확인과 JPG 렌더링 검증
    - `build_all.py`: 민감한 보안 토큰/환경설정 유출 점검 및 dist/ 격리 PyInstaller 빌더

## 3. 핵심 전역 변수 및 설정값 위치
- `setting_integrated.json` (통합 설정 파일)
  - **위치**: `C:\Users\{UserName}\AppData\Local\IntegratedDataTool\setting_integrated.json`
  - **저장값**: PDF/EML 렌더 DPI, `eml_output_width`, GitHub repo/token, 우회 변환 타겟 매핑 및 마지막 경로 정보, 동기화 그룹 목록 및 선택 그룹 인덱스, 윈도우 크기 등.
  - **보안**: `github_token` 및 `sender_password` 설정값은 Windows 사용자 자격 증명 기반 DPAPI(CryptProtectData)로 암호화 보관됩니다.
  - **예약/통지**: `task_schedule_enabled`, `task_schedule_time`, `task_schedule_last_run_date`, `task_auto_email`, `smtp_server`, `smtp_port`, `sender_email`, `sender_password`, `receiver_email`, `mail_subject`, `mail_body_header`.

## 4. 특수 주의사항 및 리스크
- **Windows DPAPI 플랫폼 의존성 및 자원 해제**: 암호화에 ctypes Windows DLL(`Crypt32.dll`)을 활용하므로 비-윈도우 OS를 대비한 Fallback 로직이 필수입니다. 할당된 Native Memory 포인터는 예외 상황에서도 누수를 방지하기 위해 반드시 `try...finally` 블록에서 `LocalFree`를 호출하도록 제어합니다.
- **설정 파일 원자성 (Atomic Write)**: 동시성 쓰기나 갑작스러운 비정상 종료 시 설정 손상을 막기 위해 `.tmp` 임시 파일에 먼저 기록하고 `os.replace`로 원본을 원자적으로 덮어씁니다.
- **Playwright Chromium 좀비 프로세스 방지**: EML 이미지 렌더링 중 예외가 발생하더라도 `browser.close()`가 확실히 보장될 수 있도록 브라우저 조작 루틴을 `try...finally`로 통제합니다.
- **읽기 전용 잠금 대응**: 파일 복사 목적지에 동일 파일이 '읽기 전용' 속성으로 잠겨 있으면 `shutil.copy2`가 실패합니다. 복사 전에 `os.chmod`를 활용해 쓰기 가능 속성을 확보한 후 덮어쓰도록 처리합니다.
- **MS Office COM 프로세스 라이프사이클 통제**: Excel, Word, PowerPoint 등 COM 연동 해제 시 발생 가능한 백그라운드 프로세스 좀비화를 차단하기 위해 예외 발생 유무와 상관없이 반드시 `app.Quit()` 및 `pythoncom.CoUninitialize()`가 호출되도록 엄격히 통제합니다.
- **동기화 최신본 기준**: 버전 파일은 파일명의 `v숫자` 버전을 우선하고 같은 버전이면 수정 시간을 사용합니다. 일반 파일은 수정 시간이 최신인 파일을 선택합니다. 10초 이내 수정이고 크기가 다르면 충돌본을 `to be deleted`에 보존한 뒤 같은 실행에서 최신본을 배포합니다.
- **예약 실행 범위**: `TaskTab`의 30초 타이머가 지정 시각 이후 당일 미실행 여부를 확인합니다. 앱이 닫혀 있거나 Windows 사용자가 로그아웃한 상태에서는 실행되지 않습니다.
- **메일 실패 처리**: SMTP 전송이 실패하면 `%LOCALAPPDATA%\IntegratedDataTool\logs\task_report_*.txt`에 원자적으로 보고서를 저장합니다.

## 5. 변경 이력
- 2026-06-18: Phase 1 ~ Phase 6 기능 통합 완료 및 6단계 누적 자가 검증 파이프라인 구축 완료. `AI_CODE_MAP.md` 최신화.
- 2026-06-18: 시니어 개발자 검수 지침에 따른 소스코드 정밀 진단 및 4대 핵심 안정성 보강(DPAPI LocalFree 보장, Atomic config write, Playwright browser release 보장, 읽기전용 우회) 완료. `AI_CODE_MAP.md` 최신화.
- 2026-06-18: 전체 소스코드 End-to-End 종합 검수 수행. 런타임 버그 3건 검출 및 교정 완료.
- 2026-06-18: UI/UX 개선 반영. 전역 PyQt 스타일 적용 및 GitHub 업데이트 저장소 설정 UI 추가.
- 2026-06-20: 다중 동기화 그룹(Sync Groups) 기능 구현, 설정 파일 마이그레이션 지원, 원클릭 전체 일괄 동기화(Sync ALL) 기능 탑재.
- 2026-06-20: EML 다중 폴더 일괄 배치 변환 기능 탑재.
- 2026-06-20: 애플리케이션 전체 UI 다크 모드(Dark Mode) 전면 개편.
- 2026-06-20: PDF 변환 및 OCR 판독 기능 완전 분리 설계 및 구현 완료.
- 2026-06-20: 전수 감사(Audit) 및 예외 방어 기능 강화(Hardening) 작업 완료.
- 2026-06-20: 포맷 우회 변환(Bypass Convert) 기능 및 UI 탭 신규 구축. MS Office COM 연동을 통한 .xlsx -> .xlsb, .pptx -> .pptm, .docx -> .docm 변환 및 PDF -> .zip 압축 변환 구현. ctypes KERNEL32 API를 활용한 파일 메타데이터(생성일, 수정일, 액세스일) 100% 강제 복원 및 보존 처리 탑재. 신규 단위 테스트(test_bypass_tab.py) 포함 전체 30개 회귀 테스트 100% 성공(OK) 완료. `AI_CODE_MAP.md` 최신화.
- 2026-06-20: 통합 일괄 순차 실행(Task Runner) 탭 및 비동기 엔진(TaskWorker) 구현 완료. SMTP 이메일 연동 및 메일 전송 실패 시 로컬 Fallback(Atomic write) 기능 추가. Settings 다이얼로그에 SMTP 설정 양식 추가 및 비밀번호 DPAPI 연동 보안 암호화 보존 적용. 신규 단위 테스트(test_email_sender.py, test_task_engine.py) 작성 완료. `AI_CODE_MAP.md` 최신화.
- 2026-06-20: 실제 프로젝트 디렉토리를 전수 점검하여 누락되어 있던 파일들(`ocr_processor.py`, `file_manager.py`, `workflow_widget.py`, `test_eml_tasks.py`)의 구조적 정보를 코드 지도에 전면 반영하여 최신화.
- 2026-06-20: 런타임 버그 교정 및 테스트 100% 패스 보강:
  - `bypass_tab.py`의 UI 락 제어 시 존재하지 않는 `self.radio_copy` 참조(AttributeError)를 `self.radio_custom`으로 수정하고, 텍스트 상자 초기값 비교 오류 교정.
  - `ocr_tab.py`에서 이미지 다중 로드 시 `itemChanged` 시그널이 중복 누적되어 연결되던 버그를 단일 바인딩으로 개선.
  - `test_task_engine.py` 테스트 실행 시 `os.path.exists`의 일률적 `True` 모킹으로 발생하던 OCR 파일 이름 충돌 방지 루프 무한 행(hang) 현상을 파일 유형별 `side_effect`로 교정하여 해결.
  - `test_gui_connections.py`에 'Task Runner' 탭 검증 인덱스를 정상 반영.
  - 전체 34개 회귀 테스트 전수 통과(OK) 최종 확인.
- 2026-06-21: 프로젝트 목적을 팀 간 자료 배포 허브, 정산 자료 전처리, 예약 실행·결과 통지 중심으로 재정의하고 `README.md`, `task.md`, `walkthrough.md`를 추가.
- 2026-06-21: 동기화 충돌본 백업 후 최신본 즉시 배포, 통합/개별 워커 부분 실패 판정, EML 증분 처리·HTML 이스케이프, ConfigManager 기본값 격리·보안 키 평문 저장 차단, PDF 자원 해제를 보강.
- 2026-06-21: 앱 실행 중 일일 예약 실행과 이메일 결과 통지를 추가하고 실제 PDF 렌더링을 포함한 회귀 테스트를 46개로 확대.

