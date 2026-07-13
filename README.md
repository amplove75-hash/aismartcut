# AI 스마트 캡처 (2단계: 기본 캡처 + 저장/클립보드)

OCR·저장·복사·AI 이미지 검색을 하나의 앱으로 통합하는 "AI 스마트 캡처" 프로젝트의
2단계 실행본입니다. 계획서의 개발 단계 중 아래 기능까지 구현되어 있습니다.

- 마우스 드래그로 화면 영역 캡처
- 주 모니터 전체 화면 캡처
- 캡처 취소 (Esc 키 또는 우클릭)
- 캡처 이미지 미리보기 및 확대/축소
- PNG/JPG 파일로 저장 (확장자 자동 처리, 저장 오류 안내)
- 클립보드로 복사 (Ctrl+C) / 클립보드에서 붙여넣기 (Ctrl+V)

## 실행 방법 (Windows, PySide6는 로컬 데스크톱에서만 동작합니다)

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Python 3.11 이상을 권장합니다.

## 폴더 구조

```
ai_smart_capture/
  main.py                 앱 실행 진입점
  capture/
    screen_capture.py     화면 캡처(QScreen) 저수준 기능
    overlay.py             드래그 영역 선택 오버레이
  storage/
    file_manager.py        PNG/JPG 저장, 클립보드 복사/붙여넣기
  ui/
    main_window.py         메인 윈도우 (버튼, 상태바)
    preview_widget.py       캡처 이미지 미리보기 / 확대·축소
  requirements.txt
```

## 알려진 제한 사항

- 이번 단계는 주 모니터만 지원합니다(다중 모니터는 6단계에서 추가 예정).
- 아직 OCR/AI 분석/이미지 검색 기능은 없습니다(3~5단계에서 순차 추가 예정).

## 다음 단계 계획

1. 3단계: PaddleOCR 기반 한글·영문·숫자 인식, 결과 수정/복사/TXT 저장
2. 4단계: AI 이미지 분석(사물/장소/제품/문서 유형) 및 검색어 자동 생성
3. 5단계: 추천 검색어 기반 웹 이미지 검색, 로컬 유사 이미지 검색
4. 6단계: 전역 단축키, 다중 모니터, 캡처 기록, 주석·모자이크 편집, 트레이 아이콘, PyInstaller EXE 배포

## 향후 웹앱 확장 메모

지금은 계획서 원안대로 PySide6 데스크톱 앱으로 진행하되, OCR·AI 분석·유사 이미지 검색
로직(3~5단계)은 UI 코드와 분리된 순수 파이썬 모듈로 작성해 나중에 웹 버전(FastAPI 등)을
만들 때 그대로 재사용할 수 있게 구성할 예정입니다.
