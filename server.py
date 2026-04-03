from flask import Flask, request, jsonify, send_from_directory
import requests
import os
import threading

app = Flask(__name__, static_folder='.', static_url_path='')

MODEL_BASE_URL = 'https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights'
MODEL_FILES = {
    'tiny_face_detector_model-weights_manifest.json',
    'tiny_face_detector_model-shard1',
    'face_expression_model-weights_manifest.json',
    'face_expression_model-shard1',
    'age_gender_model-weights_manifest.json',
    'age_gender_model-shard1',
}
MODEL_DIR = os.path.join(app.root_path, 'weights')
MODEL_LOCK = threading.Lock()


def ensure_weight_file(filename):
    if filename not in MODEL_FILES:
        return False, 'Unknown model file requested'

    os.makedirs(MODEL_DIR, exist_ok=True)
    local_path = os.path.join(MODEL_DIR, filename)
    if os.path.exists(local_path):
        return True, None

    # Protect download so concurrent requests do not race on the same file.
    with MODEL_LOCK:
        if os.path.exists(local_path):
            return True, None

        try:
            url = f'{MODEL_BASE_URL}/{filename}'
            res = requests.get(url, timeout=45)
            if res.status_code != 200:
                return False, f'Failed to download model ({res.status_code})'

            temp_path = f'{local_path}.part'
            with open(temp_path, 'wb') as f:
                f.write(res.content)
            os.replace(temp_path, local_path)
            return True, None
        except Exception as e:
            return False, str(e)

@app.route('/weights/<path:filename>')
def weights(filename):
    ok, err = ensure_weight_file(filename)
    if not ok:
        status = 404 if 'Unknown model file' in (err or '') else 502
        return jsonify({'error': err}), status
    return send_from_directory('weights', filename)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/gemini', methods=['POST'])
def gemini():
    data = request.json
    key = data.get('key')
    body = data.get('body')

    if not key or not body:
        return jsonify({'error': 'Missing key or body'}), 400

    try:
        res = requests.post(
            f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}',
            json=body,
            timeout=15
        )
        return jsonify(res.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f'\nMirror Mirror running at http://localhost:{port}\n')
    app.run(host='0.0.0.0', port=port, debug=False)
