"""AI 스마트 캡처 - 실행 진입점 (4단계: 기본 캡처 + 저장/클립보드 + OCR + AI 분석)."""
from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow
from ui.style import APP_STYLESHEET


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_STYLESHEET)
    # 트레이 아이콘으로 최소화하는 창이 있으므로, 창을 숨겨도 앱이 종료되지 않게 한다.
    app.setQuitOnLastWindowClosed(False)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
