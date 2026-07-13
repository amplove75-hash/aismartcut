"""이미지 저장(PNG/JPG) 및 클립보드 복사/붙여넣기 기능."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtGui import QClipboard, QGuiApplication, QPixmap


class SaveError(Exception):
    """이미지 저장에 실패했을 때 발생하는 예외."""


def default_filename(extension: str = "png") -> str:
    """현재 시각 기반 기본 파일명을 생성한다. 예: capture_20260713_153000.png"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"capture_{timestamp}.{extension}"


def save_pixmap(pixmap: QPixmap, file_path: str) -> Path:
    """픽스맵을 PNG 또는 JPG로 저장한다.

    확장자가 없거나 지원하지 않는 확장자면 자동으로 .png를 붙인다.

    Raises:
        SaveError: 저장에 실패한 경우.
    """
    path = Path(file_path)
    if path.suffix.lower() not in (".png", ".jpg", ".jpeg"):
        path = path.with_suffix(".png")

    image_format = "PNG" if path.suffix.lower() == ".png" else "JPG"

    path.parent.mkdir(parents=True, exist_ok=True)
    ok = pixmap.save(str(path), image_format)
    if not ok:
        raise SaveError(f"이미지를 저장하지 못했습니다: {path}")
    return path


def save_text(text: str, file_path: str) -> Path:
    """텍스트를 TXT 파일로 저장한다. 확장자가 없으면 .txt를 붙인다.

    Raises:
        SaveError: 저장에 실패한 경우.
    """
    path = Path(file_path)
    if path.suffix.lower() != ".txt":
        path = path.with_suffix(".txt")

    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(text, encoding="utf-8")
    except OSError as exc:
        raise SaveError(f"텍스트를 저장하지 못했습니다: {path}") from exc
    return path


def copy_to_clipboard(pixmap: QPixmap) -> None:
    """픽스맵을 시스템 클립보드로 복사한다."""
    clipboard: QClipboard = QGuiApplication.clipboard()
    clipboard.setPixmap(pixmap)


def paste_from_clipboard() -> QPixmap | None:
    """클립보드에 이미지가 있으면 QPixmap으로, 없으면 None을 반환한다."""
    clipboard: QClipboard = QGuiApplication.clipboard()
    image = clipboard.image()
    if image.isNull():
        return None
    return QPixmap.fromImage(image)
