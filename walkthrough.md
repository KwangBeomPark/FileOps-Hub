# 2026-06-26 구조 개편 및 방어 점검 결과

## 점검 범위

- 통합 실행 아키텍처: 탭 raw dict 연결을 명시적 RunConfig/RunPlan 계약으로 교체
- 실행 엔진 분리: PyQt 없는 `TaskRunner`와 QThread 어댑터 `TaskWorker` 분리
- 외부 의존성 preflight: OCR, Playwright, Office COM, SMTP 설정 점검 공통화
- 설정 보안: GitHub 토큰과 SMTP 비밀번호 DPAPI 처리 일원화, v1 설정 마이그레이션
- 설치 방어: Git 소스 다운로드, PyInstaller, Inno Setup, Playwright Chromium 준비 흐름 점검

## 주요 교정

- `src/core/task_contracts.py`를 추가해 실행 계약과 검증 예외를 고정했습니다.
- `src/core/task_runner.py`를 추가해 통합 순차 실행을 순수 core 엔진으로 분리했습니다.
- `src/ui/task_worker.py`를 추가해 Qt signal/QThread 책임만 UI 레이어에 남겼습니다.
- 각 기능 탭에 `build_run_config()`를 추가하고 `get_task_info()`는 임시 호환 래퍼로 유지했습니다.
- `BypassTab.build_run_config()`는 통합 실행 중 자동 스캔이나 메시지 박스를 띄우지 않고 현재 스캔 결과만 검증합니다.
- `src/core/preflight.py`를 추가하고 `tools/diagnose_install.py`가 같은 점검 로직을 재사용하도록 정리했습니다.
- `sender_password`를 `ConfigManager.SECURE_KEYS`에 포함하고 SettingsDialog/email_sender의 수동 암복호화를 제거했습니다.
- `tools/build_all.py`와 `tools/diagnose_install.py`가 Inno Setup 기본 설치 경로도 탐색하도록 보강했습니다.
- Tesseract가 없을 때 Windows 내장 OCR(`Windows.Media.Ocr`)로 자동 fallback하도록 보강했습니다.
- 앱 전역 Fusion 다크 팔레트와 툴팁 다크 스타일을 추가했습니다.

## 추가 테스트

- 계약 변환과 legacy dict 호환성
- 탭별 `build_run_config()` 정상/검증 실패
- `sender_password` DPAPI 암복호화와 v1 설정 마이그레이션
- OCR, Office, SMTP preflight
- Tesseract 실패 시 Windows OCR fallback
- 순수 `TaskRunner` 성공/부분 실패 report
- GitHub 업데이트 asset 선택, HTTPS/domain 방어, 불완전 다운로드 삭제

## 운영상 남은 수동 검증

- 회사 네트워크 드라이브와 OneDrive/SharePoint 동기화 지연 환경
- 실제 Microsoft Office COM 저장 형식과 파일 잠금
- 실제 SMTP 인증, 방화벽, 메일 수신자 정책
- Tesseract 설치 경로 및 실제 정산 이미지 인식률
- 새 PC에서 GitHub Release 설치 파일 다운로드, 설치, 최초 실행

## 최종 자동 검증 결과

- `python -m compileall -q src tools`: 통과
- `python -m unittest discover -s tools -p "test_*.py" -v`: 18개 통과
- `python tools/diagnose_install.py --check-browser --check-office`: 차단 이슈 없음
  - 경고: Tesseract 미설치/PATH 미설정, GitHub updater 저장소 미설정, 현재 PC의 Office COM 미등록
- `python tools/build_all.py`: PyInstaller exe 및 Inno Setup installer 빌드 성공
- `dist/IntegratedDataTool.exe` 8초 기동 스모크: 통과
- 실제 Windows OCR fallback 샘플: Tesseract 없이 `PL-ATSZ-20261234-6789` 추출 성공
- `dist/IntegratedDataTool_Setup_v1.1.1.exe` 무인 설치, 설치된 EXE 8초 기동, 무인 제거 스모크: 통과
- EXE 크기: 102,354,870 bytes
- EXE SHA-256: `2B90B29013109FF5BC658046935C5DF1C83BC794E995A9B67D838EDC78B4B80C`
- Installer 크기: 103,916,969 bytes
- Installer SHA-256: `EF316F701EC234A29E0D85CF7874794529F8D0431E458D6C54D399E2095D81A7`
