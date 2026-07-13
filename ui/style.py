"""앱 전체에 적용하는 버튼 클릭 피드백용 스타일시트."""
from __future__ import annotations

APP_STYLESHEET = """
QPushButton {
    padding: 6px 14px;
    border: 1px solid #B0B0B0;
    border-radius: 4px;
    background-color: #F5F5F5;
}

QPushButton:hover {
    background-color: #E6F0FF;
    border-color: #4A90E2;
}

QPushButton:pressed {
    background-color: #B8D4FF;
    border-color: #2C6FCC;
    padding-top: 7px;
    padding-left: 15px;
}

QPushButton:disabled {
    color: #A0A0A0;
    background-color: #F0F0F0;
    border-color: #D8D8D8;
}
"""
