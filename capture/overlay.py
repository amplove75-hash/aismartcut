"""전체 화면 위에 반투명 오버레이를 띄워 마우스 드래그로 캡처 영역을 선택하는 위젯."""
from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import QColor, QKeyEvent, QMouseEvent, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QWidget


class CaptureOverlay(QWidget):
    """이미 캡처된 전체 화면 이미지 위에서 사용자가 드래그로 영역을 지정하게 하는 오버레이.

    영역 선택이 끝나면 ``region_captured`` 시그널로 잘라낸 QPixmap을 전달하고,
    Esc 키나 우클릭으로 취소하면 ``capture_cancelled`` 시그널을 보낸다.
    """

    region_captured = Signal(QPixmap)
    capture_cancelled = Signal()

    def __init__(self, background: QPixmap) -> None:
        super().__init__()
        self._background = background
        # 고DPI(디스플레이 배율 125%/150% 등) 환경에서는 실제 픽셀 수(배경 픽스맵)와
        # 오버레이 위젯의 논리 좌표(마우스 좌표)가 이 비율만큼 어긋난다.
        # 이를 보정하지 않으면 캡처 영역이 확대되어 보이거나 선택 범위가 어긋난다.
        self._dpr = background.devicePixelRatio() or 1.0
        self._origin: QPoint | None = None
        self._current_rect = QRect()
        self._selecting = False

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setCursor(Qt.CursorShape.CrossCursor)

        logical_width = round(self._background.width() / self._dpr)
        logical_height = round(self._background.height() / self._dpr)
        self.setGeometry(0, 0, logical_width, logical_height)

    def _to_physical_rect(self, rect: QRect) -> QRect:
        """오버레이의 논리 좌표(rect)를 배경 픽스맵의 실제 픽셀 좌표로 변환한다."""
        return QRect(
            round(rect.x() * self._dpr),
            round(rect.y() * self._dpr),
            round(rect.width() * self._dpr),
            round(rect.height() * self._dpr),
        )

    def paintEvent(self, event) -> None:  # noqa: N802 (Qt 명명 규칙 준수)
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self._background)

        # 화면 전체에 반투명 어두운 막을 씌워 선택 영역을 강조한다.
        painter.fillRect(self.rect(), QColor(0, 0, 0, 100))

        if self._selecting and not self._current_rect.isNull():
            # 선택 영역만 원본 밝기 그대로 다시 그린다(소스 좌표는 실제 픽셀 기준).
            physical_rect = self._to_physical_rect(self._current_rect)
            painter.drawPixmap(self._current_rect, self._background, physical_rect)
            pen = QPen(QColor(0, 153, 255), 2)
            painter.setPen(pen)
            painter.drawRect(self._current_rect)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._origin = event.position().toPoint()
            self._current_rect = QRect(self._origin, self._origin)
            self._selecting = True
            self.update()
        elif event.button() == Qt.MouseButton.RightButton:
            self.close()
            self.capture_cancelled.emit()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._selecting and self._origin is not None:
            self._current_rect = QRect(self._origin, event.position().toPoint()).normalized()
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._selecting:
            self._selecting = False
            rect = self._current_rect.normalized()
            self.close()
            if rect.width() < 3 or rect.height() < 3:
                self.capture_cancelled.emit()
            else:
                physical_rect = self._to_physical_rect(rect)
                cropped = self._background.copy(physical_rect)
                cropped.setDevicePixelRatio(self._dpr)
                self.region_captured.emit(cropped)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            self.capture_cancelled.emit()
