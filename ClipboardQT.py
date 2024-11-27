"""
ClipboardQT v1.0
Created with Windsurf - The World's First Agentic IDE
"""

import sys
import pyperclip
import win32gui
import win32con
import ctypes
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QTextEdit, 
    QLabel, QWidget, QSpacerItem, QSizePolicy, QPushButton, QHBoxLayout
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QPalette, QColor, QFont, QIcon
from clipboard_translator import ClipboardTranslator

# Windows 10/11 dark mode title bar
try:
    from ctypes.wintypes import DWORD, BOOL, HRGN, HWND
    user32 = ctypes.WinDLL("user32")
    dwm = ctypes.WinDLL("dwmapi")
    
    def is_windows_11_or_greater():
        """Check if running on Windows 11 or greater"""
        try:
            version = sys.getwindowsversion()
            return (version.major > 10) or (version.major == 10 and version.build >= 22000)
        except:
            return False

    class DWMWINDOWATTRIBUTE:
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        if is_windows_11_or_greater():
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        DWMWA_CAPTION_COLOR = 35

    class DWM_WINDOW_CORNER_PREFERENCE:
        DWMWCP_DEFAULT = 0
        DWMWCP_DONOTROUND = 1
        DWMWCP_ROUND = 2
        DWMWCP_ROUNDSMALL = 3

    def set_window_dark_mode(hwnd):
        """Enable dark mode for window title bar"""
        value = ctypes.c_int(1)  # 1 = Enable dark mode
        dwm.DwmSetWindowAttribute(
            hwnd,
            DWMWINDOWATTRIBUTE.DWMWA_USE_IMMERSIVE_DARK_MODE,
            ctypes.byref(value),
            ctypes.sizeof(value)
        )
        
        # Set rounded corners for Windows 11
        if is_windows_11_or_greater():
            value = ctypes.c_int(DWM_WINDOW_CORNER_PREFERENCE.DWMWCP_ROUND)
            dwm.DwmSetWindowAttribute(
                hwnd,
                32,  # DWMWA_WINDOW_CORNER_PREFERENCE
                ctypes.byref(value),
                ctypes.sizeof(value)
            )

except ImportError:
    def set_window_dark_mode(hwnd):
        pass

class ClipboardTranslatorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ClipboardQT")
        self.setGeometry(100, 100, 800, 600)
        self.setWindowFlags(Qt.FramelessWindowHint)  # Remove window frame
        self.setWindowIcon(QIcon("icon.ico"))  # Set both window and taskbar icon
        self.setup_theme()

        # Add custom title bar
        title_bar = QWidget()
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(10, 5, 10, 5)
        title_bar.setLayout(title_layout)
        title_bar.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
            }
        """)
        title_bar.setFixedHeight(35)

        # Title label
        title_label = QLabel("ClipboardQT")
        title_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 12pt;
                font-weight: bold;
            }
        """)
        title_layout.addWidget(title_label)

        # Window controls
        btn_style = """
            QPushButton {
                background-color: transparent;
                border: none;
                color: #ffffff;
                font-family: Segoe UI;
                font-size: 14px;
                padding: 5px 10px;
                min-width: 40px;
            }
            QPushButton:hover {
                background-color: #404040;
            }
        """

        minimize_btn = QPushButton("─")
        minimize_btn.setStyleSheet(btn_style)
        minimize_btn.clicked.connect(self.showMinimized)

        maximize_btn = QPushButton("□")
        maximize_btn.setStyleSheet(btn_style)
        maximize_btn.clicked.connect(self.toggle_maximize)
        
        close_btn = QPushButton("✕")
        close_btn.setStyleSheet(btn_style + """
            QPushButton:hover {
                background-color: #c42b1c;
            }
        """)
        close_btn.clicked.connect(self.close)

        title_layout.addStretch()
        title_layout.addWidget(minimize_btn)
        title_layout.addWidget(maximize_btn)
        title_layout.addWidget(close_btn)

        # Central widget and layout
        central_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(1, 1, 1, 1)
        central_widget.setLayout(main_layout)

        # Add title bar and content
        main_layout.addWidget(title_bar)

        # Content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setSpacing(10)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_widget.setLayout(content_layout)

        # Original text label and text area
        self.original_label = QLabel("Original Text")
        self.original_label.setFont(QFont("Segoe UI", 10))
        content_layout.addWidget(self.original_label)
        
        self.original_text = QTextEdit()
        self.original_text.setFont(QFont("Segoe UI", 11))
        self.original_text.setMinimumHeight(200)
        self.original_text.textChanged.connect(self.on_text_changed)
        content_layout.addWidget(self.original_text)

        # Add some spacing
        content_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # Translated text label and text area
        self.translated_label = QLabel("Translated Text")
        self.translated_label.setFont(QFont("Segoe UI", 10))
        content_layout.addWidget(self.translated_label)
        
        self.translated_text = QTextEdit()
        self.translated_text.setFont(QFont("Segoe UI", 11))
        self.translated_text.setMinimumHeight(200)
        self.translated_text.setReadOnly(True)
        content_layout.addWidget(self.translated_text)

        # Translator and clipboard setup
        self.translator = ClipboardTranslator("http://192.168.50.95:2210")
        self.last_clipboard_text = ""

        # Clipboard monitoring timer
        self.clipboard_timer = QTimer(self)
        self.clipboard_timer.timeout.connect(self.check_clipboard)
        self.clipboard_timer.start(1000)  # Check every second

        main_layout.addWidget(content_widget)
        self.setCentralWidget(central_widget)

    def setup_theme(self):
        """Set up dark theme colors"""
        palette = QPalette()
        
        # Set background color (dark grey)
        palette.setColor(QPalette.Window, QColor("#2b2b2b"))
        palette.setColor(QPalette.WindowText, QColor("#ffffff"))
        palette.setColor(QPalette.Base, QColor("#333333"))
        palette.setColor(QPalette.AlternateBase, QColor("#3b3b3b"))
        palette.setColor(QPalette.Text, QColor("#ffffff"))
        palette.setColor(QPalette.Button, QColor("#353535"))
        palette.setColor(QPalette.ButtonText, QColor("#ffffff"))
        palette.setColor(QPalette.Highlight, QColor("#2d5a88"))
        palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
        
        self.setPalette(palette)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                border: 1px solid #444444;
            }
            QTextEdit {
                background-color: #333333;
                color: #ffffff;
                border: 1px solid #444444;
                border-radius: 4px;
                padding: 8px;
            }
            QLabel {
                color: #ffffff;
                font-weight: bold;
            }
            /* Scrollbar styling */
            QScrollBar:vertical {
                border: none;
                background: #2b2b2b;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #555555;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #666666;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            /* Horizontal scrollbar */
            QScrollBar:horizontal {
                border: none;
                background: #2b2b2b;
                height: 10px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: #555555;
                min-width: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #666666;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
        """)

    def toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if hasattr(self, 'dragPos'):
            if event.buttons() == Qt.LeftButton:
                self.move(self.pos() + event.globalPos() - self.dragPos)
                self.dragPos = event.globalPos()

    def check_clipboard(self):
        """Monitor clipboard for changes"""
        current_clipboard = pyperclip.paste()
        if current_clipboard != self.last_clipboard_text:
            self.last_clipboard_text = current_clipboard
            self.original_text.setPlainText(current_clipboard)

    def on_text_changed(self):
        """Automatically translate when original text changes"""
        text = self.original_text.toPlainText()
        if text:
            translated = self.translator.translate_text(text)
            self.translated_text.setPlainText(translated)

def main():
    app = QApplication(sys.argv)
    translator_app = ClipboardTranslatorApp()
    translator_app.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
