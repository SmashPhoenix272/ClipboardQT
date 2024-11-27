from flask import Flask, request, jsonify
from flask_cors import CORS
from QuickTranslator import load_data, convert_to_sino_vietnamese
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Load data on server startup
names2, names, viet_phrase, chinese_phien_am, _ = load_data()

# Create a ThreadPoolExecutor
executor = ThreadPoolExecutor(max_workers=4)

@app.route('/translate', methods=['POST'])
def translate():
    data = request.json
    if 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400

    chinese_text = data['text']
    translated_text = convert_to_sino_vietnamese(chinese_text, names2, names, viet_phrase, chinese_phien_am)

    return jsonify({'translatedText': translated_text})

@app.route('/translate_batch', methods=['POST'])
def translate_batch():
    data = request.json
    if 'texts' not in data or not isinstance(data['texts'], list):
        return jsonify({'error': 'Invalid input. Expected a list of texts.'}), 400

    chinese_texts = data['texts']

    # Use ThreadPoolExecutor to translate texts concurrently
    translated_texts = list(executor.map(
        lambda text: convert_to_sino_vietnamese(text, names2, names, viet_phrase, chinese_phien_am),
        chinese_texts
    ))

    return jsonify({'translatedTexts': translated_texts})

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=2210)