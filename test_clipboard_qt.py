import unittest
from unittest.mock import Mock, patch
import json
import requests
from clipboard_translator import ClipboardTranslator
from ClipboardQT import ClipboardTranslatorApp
from PyQt5.QtWidgets import QApplication
import sys

class TestClipboardTranslator(unittest.TestCase):
    def setUp(self):
        self.translator = ClipboardTranslator("http://192.168.50.95:2210")
        
    @patch('requests.post')
    def test_successful_translation(self, mock_post):
        # Mock successful API response
        mock_response = Mock()
        mock_response.json.return_value = {"translated_text": "你好"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        result = self.translator.translate_text("hello")
        self.assertEqual(result, "你好")
        mock_post.assert_called_once_with(
            "http://192.168.50.95:2210/translate",
            json={"text": "hello"}
        )

    @patch('requests.post')
    def test_failed_translation_connection_error(self, mock_post):
        # Mock connection error
        mock_post.side_effect = requests.RequestException("Connection failed")
        
        result = self.translator.translate_text("hello")
        self.assertTrue(result.startswith("Translation error"))

class TestClipboardTranslatorApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create QApplication instance
        cls.app = QApplication(sys.argv)
        
    def setUp(self):
        self.window = ClipboardTranslatorApp()
        
    def test_initial_state(self):
        self.assertEqual(self.window.windowTitle(), "Clipboard Translator")
        self.assertTrue(self.window.original_text.isReadOnly())
        self.assertTrue(self.window.translated_text.isReadOnly())
        
    @patch('clipboard_translator.ClipboardTranslator.translate_text')
    def test_translation_button_click(self, mock_translate):
        # Mock successful translation
        mock_translate.return_value = "你好"
        
        # Set original text
        self.window.original_text.setPlainText("hello")
        
        # Simulate button click
        self.window.translate_btn.click()
        
        # Check if translation was updated
        self.assertEqual(self.window.translated_text.toPlainText(), "你好")
        mock_translate.assert_called_once_with("hello")

    def test_empty_text_translation(self):
        # Clear text areas
        self.window.original_text.setPlainText("")
        self.window.translated_text.setPlainText("")
        
        # Try to translate empty text
        self.window.translate_clipboard()
        
        # Check that nothing was translated
        self.assertEqual(self.window.translated_text.toPlainText(), "")

if __name__ == '__main__':
    unittest.main()
