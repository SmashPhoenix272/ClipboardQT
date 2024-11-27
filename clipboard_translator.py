import requests
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class ClipboardTranslator:
    def __init__(self, server_url):
        self.server_url = server_url
        logger.info(f"Initialized translator with server URL: {server_url}")

    def translate_text(self, text):
        """
        Send text to QTBatchServer for translation
        
        :param text: Original text to translate
        :return: Translated text or error message
        """
        try:
            logger.debug(f"Attempting to translate text: {text}")
            logger.debug(f"Sending POST request to: {self.server_url}/translate")
            
            # Print the exact request payload
            payload = {"text": text}
            logger.debug(f"Request payload: {payload}")
            
            response = requests.post(
                f"{self.server_url}/translate", 
                json=payload,
                timeout=10
            )
            logger.debug(f"Response status code: {response.status_code}")
            logger.debug(f"Raw response content: {response.text}")
            
            response.raise_for_status()
            result = response.json()
            logger.debug(f"Parsed JSON response: {result}")
            
            # Check for different possible response formats
            translated_text = None
            if isinstance(result, dict):
                # Try different possible field names
                translated_text = (
                    result.get('translatedText') or
                    result.get('translated_text') or 
                    result.get('translation') or 
                    result.get('result') or 
                    result.get('text')
                )
            elif isinstance(result, str):
                # If response is directly the translated text
                translated_text = result
                
            if not translated_text:
                logger.error(f"Could not find translation in response. Response keys: {result.keys() if isinstance(result, dict) else 'Response is not a dictionary'}")
                return 'Translation failed: No translation in response'
                
            return translated_text
            
        except requests.RequestException as e:
            error_msg = f"Translation error: {str(e)}"
            logger.error(error_msg)
            return error_msg
        except ValueError as e:
            error_msg = f"JSON parsing error: {str(e)}"
            logger.error(error_msg)
            return error_msg
