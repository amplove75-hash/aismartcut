"""Tesseract OCR(pytesseract) 기반 한글·영문·숫자 인식 엔진 (지연 로딩 + 간단한 전처리)."""
from __future__ import annotations

import io
import shutil
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageOps
from PySide6.QtCore import QBuffer, QIODevice
from PySide6.QtGui import QPixmap

# Windows에 Tesseract-OCR을 기본 경로로 설치했을 때 자동으로 찾아보는 후보 경로들.
_WINDOWS_DEFAULT_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
]


class OcrNotAvailableError(Exception):
    """Tesseract-OCR 실행 파일 또는 pytesseract 패키지를 찾을 수 없을 때 발생한다."""


@dataclass
class OcrLine:
    """OCR로 인식된 한 줄의 텍스트."""

    text: str
    confidence: float = -1.0  # Tesseract 줄 단위 신뢰도는 별도로 계산하지 않는다.


class OcrEngine:
    """pytesseract(Tesseract-OCR)를 감싸는 래퍼. 실행 파일 경로를 지연 탐색/설정한다."""

    def __init__(self, lang: str = "kor+eng") -> None:
        self._lang = lang
        self._configured = False

    def _ensure_configured(self) -> None:
        if self._configured:
            return

        try:
            import pytesseract
        except ImportError as exc:
            raise OcrNotAvailableError(
                "pytesseract 패키지가 설치되어 있지 않습니다. "
                "'pip install pytesseract'로 설치한 뒤 다시 시도해주세요."
            ) from exc

        if shutil.which("tesseract") is None:
            for candidate in _WINDOWS_DEFAULT_PATHS:
                if Path(candidate).exists():
                    pytesseract.pytesseract.tesseract_cmd = candidate
                    break
            else:
                raise OcrNotAvailableError(
                    "Tesseract-OCR 실행 파일을 찾을 수 없습니다. "
                    "https://github.com/UB-Mannheim/tesseract/wiki 에서 설치해주세요. "
                    "설치 중 'Additional language data' 항목에서 Korean을 함께 체크해야 "
                    "한글 인식이 됩니다."
                )

        self._configured = True

    def recognize(self, pixmap: QPixmap) -> list[OcrLine]:
        """QPixmap에서 텍스트를 인식해 줄 단위 리스트로 반환한다."""
        self._ensure_configured()
        import pytesseract

        image = preprocess_for_ocr(pixmap)

        try:
            raw_text = pytesseract.image_to_string(image, lang=self._lang)
        except pytesseract.TesseractError as exc:
            raise OcrNotAvailableError(
                f"Tesseract 실행 중 오류가 발생했습니다: {exc}. "
                "한국어 언어 데이터(kor.traineddata)가 설치되어 있는지 확인해주세요."
            ) from exc

        lines = [line for line in raw_text.splitlines() if line.strip()]
        return [OcrLine(text=line) for line in lines]


def preprocess_for_ocr(pixmap: QPixmap) -> Image.Image:
    """OCR 인식률을 높이기 위해 그레이스케일 변환, 확대, 대비 보정을 수행한다."""
    image = _qpixmap_to_pil(pixmap).convert("L")

    # 글자가 너무 작으면 인식률이 떨어지므로, 짧은 변이 900px 미만이면 확대한다.
    min_side = min(image.width, image.height)
    if 0 < min_side < 900:
        scale = 900 / min_side
        image = image.resize(
            (max(1, round(image.width * scale)), max(1, round(image.height * scale))),
            Image.LANCZOS,
        )

    return ImageOps.autocontrast(image)


def _qpixmap_to_pil(pixmap: QPixmap) -> Image.Image:
    """QPixmap을 PIL Image로 변환한다."""
    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.ReadWrite)
    pixmap.save(buffer, "PNG")
    data = bytes(buffer.data())
    buffer.close()
    return Image.open(io.BytesIO(data)).convert("RGB")
