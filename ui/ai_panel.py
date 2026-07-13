"""AI 이미지 분석 결과(설명·핵심 키워드·추천 검색어)를 보여주는 패널."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class AiAnalysisPanel(QWidget):
    """이미지 설명, 핵심 키워드, 추천 검색어를 표시하는 읽기 전용 패널."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._description_edit = QPlainTextEdit()
        self._description_edit.setPlaceholderText(
            "캡처 이미지에서 'AI 분석 실행'을 누르면 이미지 설명이 여기에 표시됩니다."
        )
        self._description_edit.setReadOnly(True)

        self._keywords_edit = QLineEdit()
        self._keywords_edit.setReadOnly(True)

        self._search_terms_edit = QLineEdit()
        self._search_terms_edit.setReadOnly(True)

        self.copy_search_terms_btn = QPushButton("추천 검색어 복사")

        self._usage_label = QLabel("")
        self._usage_label.setStyleSheet("color: #666666;")

        button_row = QHBoxLayout()
        button_row.addWidget(self.copy_search_terms_btn)
        button_row.addStretch(1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel("이미지 설명"))
        layout.addWidget(self._description_edit, 1)
        layout.addWidget(QLabel("핵심 키워드"))
        layout.addWidget(self._keywords_edit)
        layout.addWidget(QLabel("추천 검색어"))
        layout.addWidget(self._search_terms_edit)
        layout.addLayout(button_row)
        layout.addWidget(self._usage_label)

    def set_result(self, description: str, keywords: list[str], search_terms: list[str]) -> None:
        self._description_edit.setPlainText(description)
        self._keywords_edit.setText(", ".join(keywords))
        self._search_terms_edit.setText(", ".join(search_terms))

    def set_usage(
        self,
        input_tokens: int,
        output_tokens: int,
        total_tokens: int,
        estimated_cost_usd: float | None,
    ) -> None:
        """이번 호출의 토큰 사용량과 예상 비용을 표시한다."""
        if estimated_cost_usd is not None:
            cost_text = f"약 ${estimated_cost_usd:.5f}"
        else:
            cost_text = "비용 추정 불가(알 수 없는 모델)"

        self._usage_label.setText(
            f"이번 호출 사용량 — 입력 {input_tokens:,}토큰 · 출력 {output_tokens:,}토큰 "
            f"· 합계 {total_tokens:,}토큰 · 예상 비용 {cost_text} "
            "(참고용 추정치, 실제 청구 금액은 OpenAI 대시보드 기준)"
        )

    def search_terms_text(self) -> str:
        return self._search_terms_edit.text()

    def clear(self) -> None:
        self._description_edit.clear()
        self._keywords_edit.clear()
        self._search_terms_edit.clear()
        self._usage_label.clear()
