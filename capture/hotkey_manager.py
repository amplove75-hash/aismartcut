"""전역(글로벌) 단축키 등록/해제를 담당하는 모듈.

Qt 위젯은 GUI 스레드에서만 안전하게 다룰 수 있는데, `keyboard` 라이브러리의 콜백은
별도 리스너 스레드에서 호출된다. 그래서 콜백에서는 Qt 위젯을 직접 건드리지 않고
Signal만 발생시키고, Qt가 자동으로 이를 GUI 스레드로 안전하게 넘겨주도록 한다.
"""
from __future__ import annotations

from PySide6.QtCore import QObject, Signal


class GlobalHotkeyManager(QObject):
    """전역 단축키가 눌리면 Qt 시그널을 발생시키는 관리자."""

    region_capture_requested = Signal()
    fullscreen_capture_requested = Signal()

    def __init__(
        self,
        region_hotkey: str = "ctrl+alt+s",
        fullscreen_hotkey: str = "ctrl+alt+f",
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._region_hotkey = region_hotkey
        self._fullscreen_hotkey = fullscreen_hotkey
        self._registered = False

    def start(self) -> bool:
        """전역 단축키를 등록한다.

        `keyboard` 패키지가 없거나 등록에 실패해도 앱 실행 자체는 계속되도록
        예외를 삼키고 False를 반환한다.
        """
        try:
            import keyboard
        except ImportError:
            self._registered = False
            return False

        try:
            keyboard.add_hotkey(
                self._region_hotkey,
                lambda: self.region_capture_requested.emit(),
            )
            keyboard.add_hotkey(
                self._fullscreen_hotkey,
                lambda: self.fullscreen_capture_requested.emit(),
            )
            self._registered = True
        except Exception:
            self._registered = False

        return self._registered

    def stop(self) -> None:
        """등록했던 전역 단축키를 해제한다."""
        if not self._registered:
            return

        try:
            import keyboard

            keyboard.remove_hotkey(self._region_hotkey)
            keyboard.remove_hotkey(self._fullscreen_hotkey)
        except Exception:
            pass

        self._registered = False

    @property
    def is_registered(self) -> bool:
        return self._registered

    @property
    def region_hotkey(self) -> str:
        return self._region_hotkey

    @property
    def fullscreen_hotkey(self) -> str:
        return self._fullscreen_hotkey
