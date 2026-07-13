"""시스템 트레이 아이콘(코드로 그린 아이콘 + 열기/캡처/종료 메뉴)."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QMenu, QSystemTrayIcon, QWidget


def build_app_icon() -> QIcon:
    """외부 이미지 파일 없이 코드로 간단한 카메라 모양 아이콘을 그려서 반환한다."""
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)

    # 카메라 몸체
    painter.setBrush(QColor("#2C6FCC"))
    painter.drawRoundedRect(6, 16, 52, 36, 8, 8)

    # 카메라 위쪽 뷰파인더 돌출부
    painter.drawRoundedRect(22, 8, 20, 10, 3, 3)

    # 렌즈
    painter.setBrush(QColor("#FFFFFF"))
    painter.drawEllipse(20, 22, 24, 24)
    painter.setBrush(QColor("#2C6FCC"))
    painter.drawEllipse(28, 30, 8, 8)

    painter.end()
    return QIcon(pixmap)


class TrayIcon(QSystemTrayIcon):
    """열기 / 영역 캡처 / 전체 화면 캡처 / 종료 메뉴를 가진 트레이 아이콘."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(build_app_icon(), parent)
        self.setToolTip("AI 스마트 캡처")

        menu = QMenu(parent)
        self.open_action = QAction("열기", parent)
        self.region_capture_action = QAction("영역 캡처", parent)
        self.fullscreen_capture_action = QAction("전체 화면 캡처", parent)
        self.quit_action = QAction("종료", parent)

        menu.addAction(self.open_action)
        menu.addSeparator()
        menu.addAction(self.region_capture_action)
        menu.addAction(self.fullscreen_capture_action)
        menu.addSeparator()
        menu.addAction(self.quit_action)

        self.setContextMenu(menu)
