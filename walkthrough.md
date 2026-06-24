# 2026-06-21 전수 점검 결과

## 점검 범위
- `src/` 전체 코어·GUI 연결과 `tools/` 회귀 테스트 감사
- Python 컴파일, Ruff 정적 검사, 실제 PDF/EML 렌더링, PyQt 오프스크린 GUI 기동
- 동기화 충돌, DPAPI 설정, SMTP 모킹, Office COM 모킹, PyInstaller 빌드 점검

## 주요 교정
- 통합 실행과 EML/OCR/포맷 변환 워커가 일부 실패를 전체 성공으로 보고하던 판정 수정
- 일반 파일 동시 수정 충돌 시 충돌본만 이동하고 최신본 배포가 다음 실행까지 지연되던 문제 수정
- 앱 실행 중 매일 지정 시각에 한 번 실행하는 예약 기능과 옵션 영속화 추가
- 성공 여부와 무관하게 결과 보고서가 있으면 이메일 발송 또는 로컬 Fallback 저장
- 변경 없는 EML의 재렌더링을 생략하도록 증분 변환 설정 연결
- 일반 텍스트 EML의 `&`, `<`, `>` HTML 이스케이프 처리
- `ConfigManager` 가변 기본값 공유와 암호화 실패 시 보안 키 평문 저장 가능성 차단
- PDF 문서 핸들을 예외 시에도 닫도록 컨텍스트 관리 적용
- Windows 빌드 의존성 `pywin32`, `PyInstaller` 명시

## 추가 테스트
- 실제 1페이지 PDF -> JPG 렌더링
- EML 증분 스킵과 평문 HTML 이스케이프
- 동기화 충돌 백업 후 동일 실행 내 최신본 배포
- 설정 기본값 격리와 암호화 실패 보안
- 통합/개별 워커 부분 실패 판정
- 일일 예약 실행 중복 방지

## 운영상 남은 수동 검증
- 회사 네트워크 드라이브와 OneDrive/SharePoint 동기화 지연 환경
- 실제 Microsoft Office COM 저장 형식과 파일 잠금
- 실제 SMTP 인증, 방화벽, 메일 수신자 정책
- Tesseract 설치 경로 및 실제 정산 이미지 인식률
- 앱 종료 상태에서도 실행해야 할 경우 Windows 작업 스케줄러 연동

## 최종 자동 검증 결과
- `python -m unittest discover -s tools -p "test_*.py"`: 46개 통과
- `python -m compileall -q src tools`: 통과
- `python -m ruff check src tools --select E9,F,B`: 통과, 지적 0건
- `python tools/build_all.py`: 보안 사전 검사 및 PyInstaller 빌드 성공
- `dist/release/IntegratedDataTool.exe`: 격리 설정으로 8초 기동 스모크 성공
- EXE 크기: 124,970,830 bytes
- EXE SHA-256: `491281061A784A4A0378E7392A648483E6BF684AB24DA0F186EC1D65DE877990`
