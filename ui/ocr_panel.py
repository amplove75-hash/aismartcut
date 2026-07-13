"""OCR 인식 결과를 보여주고 수정/복사/저장할 수 있는 패널."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class OcrPanel(QWidget):
    """OCR 인식 결과 표시/편집 + 복사·TXT 저장 버튼을 담은 패널."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        title_label = QLabel("OCR 인식 결과")

        self._text_edit = QPlainTextEdit()
        self._text_edit.setPlaceholderText(
            "캡처 이미지에서 'OCR 실행'을 누르면 인식된 텍스트가 여기에 표시됩니다.\n"
            "이 창에서 바로 수정할 수 있습니다."
        )

        self.copy_btn = QPushButton("전체 복사")
        self.save_txt_btn = QPushButton("TXT로 저장")

        button_row = QHBoxLayout()
        button_row.addWidget(self.copy_btn)
        button_row.addWidget(self.save_txt_btn)
        button_row.addStretch(1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(title_label)
        layout.addWidget(self._text_edit, 1)
        layout.addLayout(button_row)

    def set_text(self, text: str) -> None:
        self._text_edit.setPlainText(text)

    def text(self) -> str:
        return self._text_edit.toPlainText()

    def clear(self) -> None:
        self._text_edit.clear()
