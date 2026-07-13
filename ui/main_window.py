"""AI 스마트 캡처 메인 윈도우 (기본 캡처 + 저장/클립보드 + OCR + AI 분석 + 트레이/전역 단축키)."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent, QGuiApplication, QKeySequence, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStatusBar,
    QSystemTrayIcon,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ai.image_analyzer import AiNotConfiguredError, ImageAnalyzer
from capture.hotkey_manager import GlobalHotkeyManager
from capture.overlay import CaptureOverlay
from capture.screen_capture import grab_primary_screen
from ocr.ocr_engine import OcrEngine, OcrNotAvailableError
from storage.file_manager import (
    SaveError,
    copy_to_clipboard,
    default_filename,
    paste_from_clipboard,
    save_pixmap,
    save_text,
)
from ui.ai_panel import AiAnalysisPanel
from ui.ocr_panel import OcrPanel
from ui.preview_widget import PreviewWidget
from ui.tray_icon import TrayIcon, build_app_icon


class MainWindow(QMainWindow):
    """6단계 일부(트레이 아이콘 + 전역 단축키)까지 포함한 메인 윈도우."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(
            "AI 스마트 캡처 - 기본 캡처 + 저장/클립보드 + OCR + AI 분석 + 트레이/단축키"
        )
        self.setWindowIcon(build_app_icon())
        self.resize(1280, 720)

        self._overlay: CaptureOverlay | None = None
        self._last_save_dir = str(Path.home())
        self._ocr_engine = OcrEngine()
        self._ai_analyzer = ImageAnalyzer()
        self._tray_notice_shown = False
        self._quitting = False

        self._preview = PreviewWidget()
        self._ocr_panel = OcrPanel()
        self._ai_panel = AiAnalysisPanel()

        self._result_tabs = QTabWidget()
        self._result_tabs.addTab(self._ocr_panel, "OCR 결과")
        self._result_tabs.addTab(self._ai_panel, "AI 분석 결과")

        self._region_btn = QPushButton("영역 캡처")
        self._fullscreen_btn = QPushButton("전체 화면 캡처")
        self._save_btn = QPushButton("저장")
        self._copy_btn = QPushButton("복사")
        self._paste_btn = QPushButton("붙여넣기")
        self._ocr_btn = QPushButton("OCR 실행")
        self._ai_btn = QPushButton("AI 분석 실행")
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
        self._ocr_btn.clicked.connect(self._run_ocr)
        self._ai_btn.clicked.connect(self._run_ai_analysis)
        self._zoom_in_btn.clicked.connect(self._preview.zoom_in)
        self._zoom_out_btn.clicked.connect(self._preview.zoom_out)
        self._zoom_reset_btn.clicked.connect(self._preview.zoom_reset)

        self._ocr_panel.copy_btn.clicked.connect(self._copy_ocr_text)
        self._ocr_panel.save_txt_btn.clicked.connect(self._save_ocr_text)
        self._ai_panel.copy_search_terms_btn.clicked.connect(self._copy_ai_search_terms)

        capture_row = QHBoxLayout()
        capture_row.addWidget(self._region_btn)
        capture_row.addWidget(self._fullscreen_btn)
        capture_row.addWidget(self._paste_btn)
        capture_row.addStretch(1)

        edit_row = QHBoxLayout()
        edit_row.addWidget(self._save_btn)
        edit_row.addWidget(self._copy_btn)
        edit_row.addWidget(self._ocr_btn)
        edit_row.addWidget(self._ai_btn)
        edit_row.addStretch(1)
        edit_row.addWidget(self._zoom_out_btn)
        edit_row.addWidget(self._zoom_reset_btn)
        edit_row.addWidget(self._zoom_in_btn)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._preview)
        splitter.addWidget(self._result_tabs)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addLayout(capture_row)
        layout.addLayout(edit_row)
        layout.addWidget(splitter, 1)
        self.setCentralWidget(central)

        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("준비 완료 - 영역 캡처 또는 전체 화면 캡처를 눌러주세요.")

        self._setup_tray_icon()
        self._setup_global_hotkeys()

    def _setup_tray_icon(self) -> None:
        """시스템 트레이 아이콘과 메뉴(열기/캡처/종료)를 구성한다."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self._tray_icon = None
            return

        self._tray_icon = TrayIcon(self)
        self._tray_icon.open_action.triggered.connect(self._restore_from_tray)
        self._tray_icon.region_capture_action.triggered.connect(self._start_region_capture)
        self._tray_icon.fullscreen_capture_action.triggered.connect(self._capture_fullscreen)
        self._tray_icon.quit_action.triggered.connect(self._quit_app)
        self._tray_icon.activated.connect(self._on_tray_activated)
        self._tray_icon.show()

    def _setup_global_hotkeys(self) -> None:
        """전역 단축키(Ctrl+Alt+S / Ctrl+Alt+F)를 등록한다."""
        self._hotkey_manager = GlobalHotkeyManager()
        self._hotkey_manager.region_capture_requested.connect(self._start_region_capture)
        self._hotkey_manager.fullscreen_capture_requested.connect(self._capture_fullscreen)
        registered = self._hotkey_manager.start()
        if registered:
            self.statusBar().showMessage(
                f"전역 단축키 등록 완료 (영역: {self._hotkey_manager.region_hotkey}, "
                f"전체화면: {self._hotkey_manager.fullscreen_hotkey})",
                5000,
            )
        else:
            self.statusBar().showMessage(
                "전역 단축키 등록 실패 - 'keyboard' 패키지 설치 여부나 관리자 권한을 확인해주세요.",
                5000,
            )

    def _restore_from_tray(self) -> None:
        self.show()
        self.raise_()
        self.activateWindow()

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self._restore_from_tray()

    def _quit_app(self) -> None:
        """트레이 메뉴의 '종료'를 눌렀을 때 실제로 앱을 완전히 끝낸다."""
        self._quitting = True
        self._hotkey_manager.stop()
        if self._tray_icon is not None:
            self._tray_icon.hide()
        QApplication.instance().quit()

    def closeEvent(self, event: QCloseEvent) -> None:
        """창 닫기(X) 버튼을 누르면 종료하지 않고 트레이로 최소화한다."""
        if self._quitting or self._tray_icon is None:
            event.accept()
            return

        event.ignore()
        self.hide()
        if not self._tray_notice_shown:
            self._tray_icon.showMessage(
                "AI 스마트 캡처",
                "트레이로 최소화되었습니다. 완전히 종료하려면 트레이 아이콘에서 '종료'를 선택하세요.",
                QSystemTrayIcon.MessageIcon.Information,
                3000,
            )
            self._tray_notice_shown = True

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

    def _run_ocr(self) -> None:
        """현재 미리보기 이미지에서 한글·영문·숫자를 인식한다."""
        pixmap = self._preview.current_pixmap
        if pixmap is None:
            QMessageBox.information(self, "OCR", "OCR을 실행할 캡처 이미지가 없습니다.")
            return

        self.statusBar().showMessage(
            "OCR 인식 중입니다... (처음 실행 시 모델을 내려받고 불러오느라 시간이 걸릴 수 있어요)"
        )
        QApplication.processEvents()

        try:
            lines = self._ocr_engine.recognize(pixmap)
        except OcrNotAvailableError as exc:
            QMessageBox.warning(self, "OCR 오류", str(exc))
            self.statusBar().showMessage("OCR 실행 실패", 5000)
            return
        except Exception as exc:  # noqa: BLE001 - OCR 엔진 예외를 그대로 사용자에게 안내
            QMessageBox.warning(self, "OCR 오류", f"OCR 인식 중 오류가 발생했습니다: {exc}")
            self.statusBar().showMessage("OCR 실행 실패", 5000)
            return

        text = "\n".join(line.text for line in lines)
        self._ocr_panel.set_text(text)
        self._result_tabs.setCurrentWidget(self._ocr_panel)
        self.statusBar().showMessage(f"OCR 인식 완료 ({len(lines)}줄)", 5000)

    def _copy_ocr_text(self) -> None:
        """OCR 결과 텍스트 전체를 클립보드로 복사한다."""
        text = self._ocr_panel.text()
        if not text.strip():
            QMessageBox.information(self, "복사", "복사할 OCR 텍스트가 없습니다.")
            return
        QGuiApplication.clipboard().setText(text)
        self.statusBar().showMessage("OCR 텍스트를 클립보드로 복사했습니다.", 3000)

    def _save_ocr_text(self) -> None:
        """OCR 결과 텍스트를 TXT 파일로 저장한다."""
        text = self._ocr_panel.text()
        if not text.strip():
            QMessageBox.information(self, "저장", "저장할 OCR 텍스트가 없습니다.")
            return

        default_path = str(Path(self._last_save_dir) / default_filename("txt"))
        file_path, _ = QFileDialog.getSaveFileName(
            self, "OCR 텍스트 저장", default_path, "텍스트 파일 (*.txt)"
        )
        if not file_path:
            return

        try:
            saved_path = save_text(text, file_path)
        except SaveError as exc:
            QMessageBox.warning(self, "저장 오류", str(exc))
            return

        self._last_save_dir = str(saved_path.parent)
        self.statusBar().showMessage(f"OCR 텍스트 저장 완료: {saved_path}", 5000)

    def _run_ai_analysis(self) -> None:
        """현재 미리보기 이미지를 AI로 분석해 설명/키워드/추천 검색어를 얻는다."""
        pixmap = self._preview.current_pixmap
        if pixmap is None:
            QMessageBox.information(self, "AI 분석", "분석할 캡처 이미지가 없습니다.")
            return

        self.statusBar().showMessage("AI 분석 중입니다... (API 응답까지 몇 초 걸릴 수 있어요)")
        QApplication.processEvents()

        try:
            result = self._ai_analyzer.analyze(pixmap)
        except AiNotConfiguredError as exc:
            QMessageBox.warning(self, "AI 분석 오류", str(exc))
            self.statusBar().showMessage("AI 분석 실패", 5000)
            return
        except Exception as exc:  # noqa: BLE001 - API 예외를 그대로 사용자에게 안내
            QMessageBox.warning(self, "AI 분석 오류", f"AI 분석 중 오류가 발생했습니다: {exc}")
            self.statusBar().showMessage("AI 분석 실패", 5000)
            return

        self._ai_panel.set_result(result.description, result.keywords, result.search_terms)
        self._ai_panel.set_usage(
            result.input_tokens,
            result.output_tokens,
            result.total_tokens,
            result.estimated_cost_usd,
        )
        self._result_tabs.setCurrentWidget(self._ai_panel)
        self.statusBar().showMessage("AI 분석 완료", 5000)

    def _copy_ai_search_terms(self) -> None:
        """AI가 추천한 검색어를 클립보드로 복사한다."""
        text = self._ai_panel.search_terms_text()
        if not text.strip():
            QMessageBox.information(self, "복사", "복사할 추천 검색어가 없습니다.")
            return
        QGuiApplication.clipboard().setText(text)
        self.statusBar().showMessage("추천 검색어를 클립보드로 복사했습니다.", 3000)
