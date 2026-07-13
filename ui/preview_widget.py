"""캡처 결과 미리보기 및 확대/축소를 담당하는 위젯."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QScrollArea, QSizePolicy, QVBoxLayout, QWidget


class PreviewWidget(QWidget):
    """QScrollArea 안에 이미지를 표시하고 배율 조정을 지원한다."""

    MIN_SCALE = 0.1
    MAX_SCALE = 5.0
    SCALE_STEP = 0.1

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._original_pixmap: QPixmap | None = None
        self._scale = 1.0

        self._image_label = QLabel("캡처된 이미지가 여기에 표시됩니다.")
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_label.setSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored
        )

        self._scroll_area = QScrollArea()
        self._scroll_area.setWidget(self._image_label)
        self._scroll_area.setWidgetResizable(False)
        self._scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._scroll_area)

    @property
    def current_pixmap(self) -> QPixmap | None:
        """현재 표시 중인 원본(비확대) 픽스맵을 반환한다."""
        return self._original_pixmap

    def set_pixmap(self, pixmap: QPixmap) -> None:
        """새 캡처 이미지를 표시하고 배율/스크롤 위치를 초기 상태로 되돌린다."""
        self._original_pixmap = pixmap
        self._scale = 1.0
        self._render()
        self._reset_scroll_position()

    def clear(self) -> None:
        self._original_pixmap = None
        self._image_label.setText("캡처된 이미지가 여기에 표시됩니다.")
        self._image_label.setPixmap(QPixmap())

    def zoom_in(self) -> None:
        self._set_scale(self._scale + self.SCALE_STEP)

    def zoom_out(self) -> None:
        self._set_scale(self._scale - self.SCALE_STEP)

    def zoom_reset(self) -> None:
        """배율을 100%로 되돌리고, 스크롤 위치도 캡처 직후 상태(원래 위치)로 되돌린다."""
        if self._original_pixmap is None:
            return
        self._scale = 1.0
        self._render()
        self._reset_scroll_position()

    def _reset_scroll_position(self) -> None:
        self._scroll_area.horizontalScrollBar().setValue(0)
        self._scroll_area.verticalScrollBar().setValue(0)

    def _set_scale(self, scale: float) -> None:
        """확대/축소 시 보고 있던 지점(스크롤 위치)을 유지한 채 배율만 바꾼다."""
        if self._original_pixmap is None:
            return
        new_scale = max(self.MIN_SCALE, min(self.MAX_SCALE, scale))
        if new_scale == self._scale:
            return
        factor = new_scale / self._scale
        self._scale = new_scale
        self._render()
        self._adjust_scrollbar(self._scroll_area.horizontalScrollBar(), factor)
        self._adjust_scrollbar(self._scroll_area.verticalScrollBar(), factor)

    @staticmethod
    def _adjust_scrollbar(scrollbar, factor: float) -> None:
        """배율 변화(factor)에 맞춰 스크롤 위치를 같이 조정해 화면 중심이 그대로 유지되게 한다."""
        scrollbar.setValue(
            int(factor * scrollbar.value() + (factor - 1) * scrollbar.pageStep() / 2)
        )

    def _render(self) -> None:
        if self._original_pixmap is None:
            return
        size = self._original_pixmap.size() * self._scale
        scaled = self._original_pixmap.scaled(
            size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._image_label.setPixmap(scaled)
        self._image_label.resize(scaled.size())
