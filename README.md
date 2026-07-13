# AI 스마트 캡처

OCR·저장·복사·AI 이미지 검색을 하나의 앱으로 통합하는 "AI 스마트 캡처" 프로젝트입니다.
5단계(웹/로컬 유사 이미지 검색)는 건너뛰고, 6단계 중 트레이 아이콘·전역 단축키·EXE 배포까지
아래 기능이 구현되어 있습니다.

- 마우스 드래그로 화면 영역 캡처
- 주 모니터 전체 화면 캡처
- 캡처 취소 (Esc 키 또는 우클릭)
- 캡처 이미지 미리보기 및 확대/축소 (위치 이동 없이 배율만 조정)
- PNG/JPG 파일로 저장 (확장자 자동 처리, 저장 오류 안내)
- 클립보드로 복사 (Ctrl+C) / 클립보드에서 붙여넣기 (Ctrl+V)
- Tesseract OCR(pytesseract) 기반 한글·영문·숫자 인식 (그레이스케일/확대/대비 보정 전처리 포함)
- OCR 결과 수정, 전체 복사, TXT 파일 저장
- OpenAI Vision API(gpt-4o-mini) 기반 이미지 설명 + 핵심 키워드 + 추천 검색어 자동 생성 (호출당 토큰/예상 비용 표시)
- 시스템 트레이 아이콘 (닫기 버튼을 누르면 종료 대신 트레이로 최소화, 트레이 메뉴에서 열기/캡처/종료)
- 전역 단축키 (앱이 백그라운드에 있어도 동작): 영역 캡처 `Ctrl+Alt+S`, 전체 화면 캡처 `Ctrl+Alt+F`
- PyInstaller로 만든 단일 EXE 파일 배포 지원

## OpenAI API 키 설정 (필수, 최초 1회)

1. 프로젝트 폴더의 `.env.example` 파일을 복사해서 `.env`라는 이름으로 저장 (같은 폴더에)
2. `.env` 파일을 열어 `OPENAI_API_KEY=` 뒤에 발급받은 키를 붙여넣기
3. `.env`는 `.gitignore`에 포함되어 있어 깃허브에는 올라가지 않습니다 — 절대 커밋하지 마세요

## Tesseract OCR 설치 (필수, 최초 1회)

pytesseract는 Tesseract-OCR 엔진을 감싸는 파이썬 래퍼일 뿐, 엔진 본체는 별도 설치가 필요합니다.

1. https://github.com/UB-Mannheim/tesseract/wiki 에서 Windows 설치 파일을 내려받아 실행
2. 설치 중 "Additional language data" 항목에서 **Korean**을 반드시 함께 체크 (기본은 영어만 설치됨)
3. 설치 후 `pip install -r requirements.txt`로 pytesseract를 설치하면 준비 완료

기본 설치 경로(`C:\Program Files\Tesseract-OCR`)를 사용했다면 앱이 자동으로 찾습니다.
다른 경로에 설치했다면 실행 파일을 PATH에 추가해주세요.

※ 원래 계획서는 PaddleOCR을 명시했지만, PaddleOCR/PaddlePaddle이 최신 Python 버전(3.14)의
배포 휠을 아직 제공하지 않아 실행이 불가능해 Tesseract OCR로 대체했습니다.

## 실행 방법 (개발 중 - Windows, PySide6는 로컬 데스크톱에서만 동작합니다)

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Python 3.11 이상을 권장합니다.

## 전역 단축키 안내

- 영역 캡처: `Ctrl+Alt+S`
- 전체 화면 캡처: `Ctrl+Alt+F`

앱을 창을 닫아 트레이로 내려도(완전 종료가 아니라 최소화) 위 단축키는 계속 동작합니다.
일부 보안 프로그램이나 권한이 제한된 환경에서는 전역 단축키 등록이 실패할 수 있습니다.
그럴 경우 앱을 관리자 권한으로 실행해보거나, 상태 표시줄에 뜨는 등록 실패 메시지를 확인해주세요.

## EXE로 패키징하기 (배포용)

1. 가상환경을 활성화한 상태에서 PyInstaller를 한 번만 설치합니다 (requirements.txt에는 포함하지 않았습니다 — 개발/빌드 시에만 필요하기 때문입니다).
   ```
   pip install pyinstaller
   ```
2. 프로젝트 폴더에서 빌드합니다.
   ```
   pyinstaller --name AI스마트캡처 --onefile --windowed main.py
   ```
3. 빌드가 끝나면 `dist\AI스마트캡처.exe`가 생성됩니다.
4. **`dist` 폴더에 `.env` 파일을 직접 복사해 넣어주세요.** PyInstaller는 `.env`(개인 API 키)를
   자동으로 EXE 안에 넣지 않으며, 앱은 실행 파일과 같은 폴더에서 `.env`를 찾도록 만들어져
   있습니다.
5. 이 EXE를 받는 다른 컴퓨터에서도 **Tesseract-OCR은 별도로 설치**되어 있어야 합니다
   (pytesseract는 파이썬 래퍼일 뿐 엔진 자체를 EXE 안에 담아 배포하지 않습니다).

배포 시 다른 컴퓨터에 전달해야 할 것: `AI스마트캡처.exe` + 그 옆에 둘 `.env` 파일, 그리고
받는 쪽 컴퓨터에 Tesseract-OCR(한국어 언어 데이터 포함) 설치 안내.

## 폴더 구조

```
ai_smart_capture/
  main.py                 앱 실행 진입점
  capture/
    screen_capture.py     화면 캡처(QScreen) 저수준 기능
    overlay.py             드래그 영역 선택 오버레이
    hotkey_manager.py       전역 단축키 등록/해제 (keyboard 패키지 래퍼)
  storage/
    file_manager.py        PNG/JPG 저장, 클립보드 복사/붙여넣기, TXT 저장
  ocr/
    ocr_engine.py           Tesseract OCR(pytesseract) 래퍼 + 전처리
  ai/
    image_analyzer.py       OpenAI Vision API 래퍼(이미지 설명/키워드/검색어/사용량)
  ui/
    main_window.py         메인 윈도우 (버튼, 상태바, 좌우 분할 + 결과 탭, 트레이/단축키 연결)
    preview_widget.py       캡처 이미지 미리보기 / 확대·축소
    ocr_panel.py            OCR 결과 표시/수정/복사/저장 패널
    ai_panel.py             AI 분석 결과(설명/키워드/검색어/사용량) 표시 패널
    tray_icon.py             시스템 트레이 아이콘 + 메뉴
    style.py                 버튼 클릭 피드백용 스타일시트
  requirements.txt
  .env.example              OpenAI API 키 설정 예시 (복사해서 .env로 사용)
```

## 알려진 제한 사항

- 화면 캡처는 주 모니터만 지원합니다(다중 모니터 지원은 아직 없음).
- OCR/AI 분석 모두 API·모델 응답을 기다리는 동안 화면이 잠깐 멈춘 것처럼 보일 수 있습니다
  (백그라운드 스레드 처리는 추후 개선 예정).
- AI 분석은 OpenAI API 호출마다 비용이 발생합니다(사용량 기준 과금, 패널에 추정치 표시).
- 캡처 기록(히스토리), 주석·모자이크 편집 기능은 아직 없습니다.
- 웹 이미지 검색 연결, 로컬 유사 이미지 검색 기능(계획서 5단계)은 구현하지 않기로 했습니다.

## 향후 웹앱 확장 메모

지금은 계획서 원안대로 PySide6 데스크톱 앱으로 진행하되, OCR·AI 분석 로직은 UI 코드와
분리된 순수 파이썬 모듈로 작성해 나중에 웹 버전(FastAPI 등)을 만들 때 그대로 재사용할 수
있게 구성했습니다.
