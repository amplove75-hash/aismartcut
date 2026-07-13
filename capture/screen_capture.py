"""화면 캡처 관련 저수준 기능 (전체 화면 그랩)."""
from __future__ import annotations

from PySide6.QtGui import QPixmap, QScreen
from PySide6.QtWidgets import QApplication


def grab_primary_screen() -> QPixmap:
    """주 모니터 전체 화면을 QPixmap으로 캡처한다.

    Raises:
        RuntimeError: 사용 가능한 화면을 찾지 못한 경우.
    """
    screen: QScreen | None = QApplication.primaryScreen()
    if screen is None:
        raise RuntimeError("사용 가능한 화면(Screen)을 찾을 수 없습니다.")

    pixmap = screen.grabWindow(0)
    # 디스플레이 배율(125%, 150% 등)이 적용된 고해상도 모니터에서는 실제 픽셀 수와
    # 화면에 보이는 논리 크기가 달라서, devicePixelRatio를 붙여주지 않으면
    # 캡처 이미지가 실제보다 확대되어 보인다.
    pixmap.setDevicePixelRatio(screen.devicePixelRatio())
    return pixmap
