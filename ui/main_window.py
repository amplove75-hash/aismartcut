"""AI 스마트 캡처 메인 윈도우 (2단계: 기본 캡처 + 저장/클립보드)."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QKeySequence, QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from capture.overlay import CaptureOverlay
from capture.screen_capture import grab_primary_screen
from storage.file_manager import (
    SaveError,
    copy_to_clipboard,
    default_filename,
    paste_from_clipboard,
    save_pixmap,
)
from ui.preview_widget import PreviewWidget


class MainWindow(QMainWindow):
    """2단계 (기본 캡처 + 저장/클립보드) 앱의 메인 윈도우."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("AI 스마트 캡처 - 2단계 (기본 캡처 + 저장/클립보드)")
        self.resize(900, 650)

        self._overlay: CaptureOverlay | None = None
        self._last_save_dir = str(Path.home())

        self._preview = PreviewWidget()

        self._region_btn = QPushButton("영역 캡처")
        self._fullscreen_btn = QPushButton("전체 화면 캡처")
        self._save_btn = QPushButton("저장")
        self._copy_btn = QPushButton("복사")
        self._paste_btn = QPushButton("붙여넣기")
        self._zoom_in_btn = QPushButton("확대 (+)")
        self._zoom_out_btn = QPushButton("축소 (-)")
        self._zoom_reset_btn = QPushButton("100%")

        self._copy_btn.setShortcut(QKeySequence.StandardKey.Copy)
        self._paste_btn.setShortcut(QKeySequence.StandardKey.Paste)

        self._region_btn.clicked.connect(self._start_region_capture)
        self._fullscreen_btn.clicked.connect(self._capture_fullscreen)
        self._save_btn.clicked.connect(self._save_current_image)
        self._copy_btn.clicked.connect(self._copy_current_image)
        self._paste_btn.clicked.connect(self._paste_from_clipboard)
        self._zoom_in_btn.clicked.connect(self._preview.zoom_in)
        self._zoom_out_btn.clicked.connect(self._preview.zoom_out)
        self._zoom_reset_btn.clicked.connect(self._preview.zoom_reset)

        capture_row = QHBoxLayout()
        capture_row.addWidget(self._region_btn)
        capture_row.addWidget(self._fullscreen_btn)
        capture_row.addWidget(self._paste_btn)
        capture_row.addStretch(1)

        edit_row = QHBoxLayout()
        edit_row.addWidget(self._save_btn)
        edit_row.addWidget(self._copy_btn)
        edit_row.addStretch(1)
        edit_row.addWidget(self._zoom_out_btn)
        edit_row.addWidget(self._zoom_reset_btn)
        edit_row.addWidget(self._zoom_in_btn)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addLayout(capture_row)
        layout.addLayout(edit_row)
        layout.addWidget(self._preview, 1)
        self.setCentralWidget(central)

        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("준비 완료 - 영역 캡처 또는 전체 화면 캡처를 눌러주세요.")

    def _start_region_capture(self) -> None:
        """드래그로 캡처할 영역을 선택하는 오버레이를 띄운다."""
        try:
            background = grab_primary_screen()
        except RuntimeError as exc:
            QMessageBox.warning(self, "캡처 오류", str(exc))
            return

        self.hide()
        self._overlay = CaptureOverlay(background)
        self._overlay.region_captured.connect(self._on_capture_finished)
        self._overlay.capture_cancelled.connect(self._on_capture_cancelled)
        self._overlay.showFullScreen()

    def _capture_fullscreen(self) -> None:
        """주 모니터 전체 화면을 바로 캡처한다."""
        try:
            pixmap = grab_primary_screen()
        except RuntimeError as exc:
            QMessageBox.warning(self, "캡처 오류", str(exc))
            return
        self._on_capture_finished(pixmap)

    def _on_capture_finished(self, pixmap: QPixmap) -> None:
        self.show()
        self.raise_()
        self.activateWindow()
        self._preview.set_pixmap(pixmap)
        self.statusBar().showMessage(
            f"캡처 완료 ({pixmap.width()} x {pixmap.height()})", 5000
        )

    def _on_capture_cancelled(self) -> None:
        self.show()
        self.raise_()
        self.activateWindow()
        self.statusBar().showMessage("캡처를 취소했습니다.", 3000)

    def _save_current_image(self) -> None:
        """현재 미리보기 이미지를 PNG 또는 JPG 파일로 저장한다."""
        pixmap = self._preview.current_pixmap
        if pixmap is None:
            QMessageBox.information(self, "저장", "저장할 캡처 이미지가 없습니다.")
            return

        default_path = str(Path(self._last_save_dir) / default_filename())
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "이미지 저장",
            default_path,
            "PNG 이미지 (*.png);;JPG 이미지 (*.jpg *.jpeg)",
        )
        if not file_path:
            return

        try:
            saved_path = save_pixmap(pixmap, file_path)
        except SaveError as exc:
            QMessageBox.warning(self, "저장 오류", str(exc))
            return

        self._last_save_dir = str(saved_path.parent)
        self.statusBar().showMessage(f"저장 완료: {saved_path}", 5000)

    def _copy_current_image(self) -> None:
        """현재 미리보기 이미지를 클립보드로 복사한다."""
        pixmap = self._preview.current_pixmap
        if pixmap is None:
            QMessageBox.information(self, "복사", "복사할 캡처 이미지가 없습니다.")
            return
        copy_to_clipboard(pixmap)
        self.statusBar().showMessage("클립보드로 복사했습니다.", 3000)

    def _paste_from_clipboard(self) -> None:
        """클립보드의 이미지를 불러와 미리보기에 표시한다."""
        pixmap = paste_from_clipboard()
        if pixmap is None:
            QMessageBox.information(self, "붙여넣기", "클립보드에 이미지가 없습니다.")
            return
        self._on_capture_finished(pixmap)
        self.statusBar().showMessage("클립보드에서 이미지를 불러왔습니다.", 3000)
