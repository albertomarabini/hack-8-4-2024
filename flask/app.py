import logging
import os
import uuid
from flask import Flask, request, jsonify, send_from_directory
import threading
import time
from flask_cors import CORS
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)  # Enable CORS for all domains on all routes.

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger()

data_store = {}

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

file_registry = {}

def print_data_store():
    while True:
        time.sleep(10)
        logger.info("Current data_store contents:")
        for key, value in data_store.items():
            logger.info(f"{key} -> {value}")

def log_operation(operation, args):
    timestamp = datetime.now().strftime("%d%m%y")
    logger.info(f"{timestamp}-{operation}-data: {args}")

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify(result='No file part'), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify(result='No selected file'), 400
    if file:
        original_filename = secure_filename(file.filename)
        saved_filename = str(uuid.uuid4())
        file_path = os.path.join(UPLOAD_FOLDER, saved_filename)
        file.save(file_path)
        file_registry[saved_filename] = original_filename
        return jsonify(result='File uploaded', url=f'/download/{saved_filename}'), 201

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    try:
        if filename not in file_registry:
            return jsonify(result='File not found'), 404
        original_filename = file_registry[filename]
        return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True, download_name=original_filename)
    except Exception as e:
        app.logger.error(f"Error downloading file: {e}")
        return jsonify(result='Internal server error'), 500

@app.route('/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    if filename not in file_registry:
        return jsonify(result='File not found'), 404
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        del file_registry[filename]
        return jsonify(result='File deleted'), 200
    else:
        return jsonify(result='File not found'), 404

@app.route('/command', methods=['POST'])
def process_command():
    command = request.json.get('command')
    args = request.json.get('args', [])

    log_operation(command, args)

    if command == 'SET':
        key, value = args
        data_store[key] = value
        return jsonify(result=True)
    elif command == 'GET':
        if isinstance(args, list):
            result = {key: data_store.get(key, None) for key in args}
            # Filter out None values from result
            result = {k: v for k, v in result.items() if v is not None}
            if not result:
                result = None
        else:
            key = args
            result = data_store.get(key, None)
        return jsonify(result=result)
    elif command == 'DELETE':
        key = args[0]
        deleted = data_store.pop(key, None) is not None
        return jsonify(result=deleted)
    elif command == 'HAS':
        key = args[0]
        has_key = key in data_store
        return jsonify(result=has_key)
    elif command == 'LIST_KEYS':
        keys = list(data_store.keys())
        return jsonify(result=keys)
    elif command == 'LIST_DATA':
        data_items = list(data_store.items())
        return jsonify(result=data_items)
    elif command == 'CLEAR':
        data_store.clear()
        return jsonify(result="Data store cleared.")
    else:
        return jsonify(result='UNKNOWN_COMMAND')

if __name__ == '__main__':
    print_thread = threading.Thread(target=print_data_store, daemon=True)
    print_thread.start()

    app.run(debug=True, host='0.0.0.0', port=5000)
