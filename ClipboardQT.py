"""
ClipboardQT v2
Created with Windsurf - The World's First Agentic IDE
"""

import sys
import pyperclip
import win32gui
import win32con
import ctypes
import requests
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QTextEdit, 
    QLabel, QWidget, QSpacerItem, QSizePolicy, QPushButton, QHBoxLayout,
    QStyle, QStyleFactory, QLineEdit, QMessageBox, QFormLayout
)
from PyQt5.QtCore import QTimer, Qt, QPoint, QSettings
from PyQt5.QtGui import QPalette, QColor, QFont, QIcon

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
        self.setMinimumSize(400, 300)  # Set minimum window size
        self.setWindowIcon(QIcon("icon.ico"))
        
        # Create settings object
        self.settings = QSettings("ClipboardQT", "ClipboardQT")
        
        # Create window first to get handle
        self.create()
        
        # Enable dark mode for the title bar
        if self.winId() is not None:
            set_window_dark_mode(int(self.winId()))
        
        self.setup_theme()

        # Central widget and layout
        central_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        central_widget.setLayout(main_layout)

        # Content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setSpacing(10)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_widget.setLayout(content_layout)

        # Server settings section
        server_widget = QWidget()
        server_layout = QHBoxLayout()
        server_layout.setContentsMargins(0, 0, 0, 0)
        server_layout.setSpacing(10)
        server_widget.setLayout(server_layout)

        # Create label
        url_label = QLabel("Server URL:")
        url_label.setFont(QFont("Segoe UI", 11))
        url_label.setFixedWidth(85)

        # Server URL input - load saved URL
        default_url = "http://192.168.50.95:2210"
        saved_url = self.settings.value("server_url", default_url)
        self.server_url = QLineEdit(saved_url)
        self.server_url.setPlaceholderText("Enter server URL")
        self.server_url.setFont(QFont("Segoe UI", 10))
        self.server_url.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Save URL when it changes
        self.server_url.editingFinished.connect(self.save_server_url)

        # Test connection button with status indicator
        self.test_button = QPushButton("Test Connection")
        self.test_button.setFont(QFont("Segoe UI", 10))
        self.test_button.clicked.connect(self.test_connection)
        self.test_button.setStyleSheet("""
            QPushButton {
                background-color: #353535;
                color: #ffffff;
                border: 1px solid #444444;
                border-radius: 4px;
                padding: 4px 10px;
                font-family: 'Segoe UI';
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
                border: 1px solid #555555;
            }
            QPushButton:pressed {
                background-color: #2d2d2d;
                border: 1px solid #333333;
            }
        """)
        self.test_button.setFixedWidth(120)  # Fixed width for consistency

        # Status indicator
        self.status_label = QLabel("●")
        self.status_label.setFont(QFont("Segoe UI", 14))
        self.status_label.setStyleSheet("""
            QLabel {
                color: #666666; 
                margin: 0;
                padding: 0;
                qproperty-alignment: AlignCenter;
            }
        """)
        
        # Create a fixed-width container for the status label
        status_container = QWidget()
        status_container.setFixedWidth(20)
        status_container_layout = QHBoxLayout(status_container)
        status_container_layout.setContentsMargins(0, 0, 0, 0)
        status_container_layout.setAlignment(Qt.AlignCenter)
        status_container_layout.addWidget(self.status_label)

        # Add widgets to layout with proper stretching
        server_layout.addWidget(url_label)
        server_layout.addWidget(self.server_url, 1)  # Add stretch factor of 1 to make it expandable
        server_layout.addWidget(self.test_button)
        server_layout.addWidget(status_container)  # Add the container instead of direct label

        content_layout.addWidget(server_widget)

        # Add a separator line
        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        separator.setStyleSheet("background-color: #444444;")
        content_layout.addWidget(separator)
        content_layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # Original text label and text area
        self.original_label = QLabel("Original Text")
        self.original_label.setFont(QFont("Segoe UI", 10))
        content_layout.addWidget(self.original_label)
        
        self.original_text = QTextEdit()
        self.original_text.setFont(QFont("Segoe UI", 11))
        self.original_text.setMinimumHeight(100)
        self.original_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
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
        self.translated_text.setMinimumHeight(100)
        self.translated_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.translated_text.setReadOnly(True)
        content_layout.addWidget(self.translated_text)

        # Add the content widget to main layout
        main_layout.addWidget(content_widget)
        self.setCentralWidget(central_widget)

        # Server URL and clipboard setup
        self.last_clipboard_text = ""

        # Clipboard monitoring timer
        self.clipboard_timer = QTimer(self)
        self.clipboard_timer.timeout.connect(self.check_clipboard)
        self.clipboard_timer.start(1000)

    def save_server_url(self):
        """Save the current server URL to settings"""
        url = self.server_url.text()
        self.settings.setValue("server_url", url)

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
            QLineEdit {
                background-color: #333333;
                color: #ffffff;
                border: 1px solid #444444;
                border-radius: 4px;
                padding: 6px;
                selection-background-color: #2d5a88;
            }
            QPushButton {
                background-color: #2d5a88;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #366ba2;
            }
            QPushButton:pressed {
                background-color: #245072;
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

    def translate_text(self, text):
        """Send text to QTEngine server for translation"""
        if not text:
            return ""
            
        url = self.server_url.text().strip()
        try:
            # Prepare request payload matching QTEngineServer
            payload = {
                "text": text,
                "options": None  # Optional parameter
            }
            
            # Send translation request
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            response = requests.post(
                f"{url}/translate", 
                json=payload,
                headers=headers,
                timeout=10
            )
            
            # Check response
            if response.status_code == 200:
                try:
                    # Parse response matching TranslationResponse model
                    result = response.json()
                    
                    # Extract translated text 
                    translation = result.get('translated_text')
                    
                    if translation:
                        return translation
                    else:
                        return "Error: No translation found in server response"
                
                except ValueError as e:
                    return f"Error parsing server response: {str(e)}"
            
            else:
                return f"Translation error: Server returned {response.status_code}"
        
        except requests.exceptions.RequestException as e:
            return f"Connection error: {str(e)}"
        
        except Exception as e:
            return f"Unexpected error: {str(e)}"

    def test_connection(self):
        """Test the connection to the translation server"""
        url = self.server_url.text().strip()
        if not url:
            self.status_label.setStyleSheet("color: #666666;")
            self.status_label.setToolTip("Please enter a server URL")
            return

        try:
            self.status_label.setStyleSheet("color: #FFA500;")
            self.status_label.setToolTip("Testing connection...")
            QApplication.processEvents()
            
            # Send test request with proper headers
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            response = requests.get(url + "/ping", headers=headers, timeout=5)
            if response.status_code == 200:
                self.status_label.setStyleSheet("color: #00FF00;")
                self.status_label.setToolTip("Connected successfully")
            else:
                self.status_label.setStyleSheet("color: #FF0000;")
                self.status_label.setToolTip(f"Server error: {response.status_code}")
        except requests.exceptions.RequestException as e:
            self.status_label.setStyleSheet("color: #FF0000;")
            self.status_label.setToolTip(f"Connection error: {str(e)}")

    def check_clipboard(self):
        """Monitor clipboard for changes"""
        try:
            clipboard_text = pyperclip.paste()
            if clipboard_text != self.last_clipboard_text:
                self.last_clipboard_text = clipboard_text
                self.original_text.setPlainText(clipboard_text)
        except:
            pass

    def on_text_changed(self):
        """Automatically translate when original text changes"""
        text = self.original_text.toPlainText()
        if text:
            translated = self.translate_text(text)
            self.translated_text.setPlainText(translated)

def main():
    """Main application entry point"""
    # Set high DPI scaling attributes
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # Create application and main window
    app = QApplication(sys.argv)
    window = ClipboardTranslatorApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
