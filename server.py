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
DEFAULT_GEMINI_MODELS = ['gemini-2.0-flash', 'gemini-1.5-flash']


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


def list_missing_weight_files():
    os.makedirs(MODEL_DIR, exist_ok=True)
    return [f for f in MODEL_FILES if not os.path.exists(os.path.join(MODEL_DIR, f))]


def parse_error_message(payload):
    if isinstance(payload, dict):
        err = payload.get('error')
        if isinstance(err, dict):
            return err.get('message') or str(err)
        if err:
            return str(err)
    return 'Unknown Gemini API error'


def model_not_found(payload):
    msg = parse_error_message(payload).lower()
    return 'model' in msg and ('not found' in msg or 'unsupported' in msg or 'invalid' in msg)


def post_gemini_generate(key, model, body):
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}'
    try:
        res = requests.post(url, json=body, timeout=25)
    except requests.RequestException as e:
        return None, None, str(e)

    try:
        payload = res.json()
    except ValueError:
        payload = {'error': {'message': f'Gemini returned non-JSON response (HTTP {res.status_code})'}}
    return res.status_code, payload, None


@app.route('/weights/<path:filename>')
def weights(filename):
    ok, err = ensure_weight_file(filename)
    if not ok:
        status = 404 if 'Unknown model file' in (err or '') else 502
        return jsonify({'error': err}), status
    return send_from_directory('weights', filename)


@app.route('/weights/status')
def weights_status():
    missing = list_missing_weight_files()
    return jsonify({
        'total': len(MODEL_FILES),
        'ready': len(MODEL_FILES) - len(missing),
        'missing': sorted(missing),
    })


@app.route('/weights/prefetch', methods=['POST'])
def weights_prefetch():
    missing = list_missing_weight_files()
    downloaded = []
    failed = []
    for filename in missing:
        ok, err = ensure_weight_file(filename)
        if ok:
            downloaded.append(filename)
        else:
            failed.append({'file': filename, 'error': err})

    return jsonify({
        'downloaded': downloaded,
        'failed': failed,
        'total': len(MODEL_FILES),
        'ready': len(MODEL_FILES) - len(list_missing_weight_files()),
    }), (207 if failed else 200)


@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


@app.route('/config')
def config():
    return jsonify({
        'serverKeyConfigured': bool(os.environ.get('GEMINI_API_KEY')),
        'defaultModel': os.environ.get('GEMINI_MODEL', DEFAULT_GEMINI_MODELS[0]),
    })


@app.route('/healthz')
def healthz():
    return jsonify({
        'status': 'ok',
        'missingWeights': len(list_missing_weight_files()),
    })


@app.route('/gemini', methods=['POST'])
def gemini():
    data = request.get_json(silent=True) or {}
    key = data.get('key') or os.environ.get('GEMINI_API_KEY')
    body = data.get('body')
    requested_model = (data.get('model') or os.environ.get('GEMINI_MODEL') or DEFAULT_GEMINI_MODELS[0]).strip()

    if not body:
        return jsonify({'error': {'message': 'Missing Gemini request body'}}), 400
    if not key:
        return jsonify({'error': {'message': 'Missing API key. Add a key in settings, or set GEMINI_API_KEY on the server.'}}), 400

    models_to_try = [requested_model] + [m for m in DEFAULT_GEMINI_MODELS if m != requested_model]
    last_status = None
    last_payload = None

    for idx, model in enumerate(models_to_try):
        status_code, payload, req_err = post_gemini_generate(key, model, body)
        if req_err:
            return jsonify({'error': {'message': f'Gemini network error: {req_err}'}}), 502

        if status_code is not None and status_code < 400:
            if isinstance(payload, dict):
                payload.setdefault('_meta', {})
                payload['_meta']['model'] = model
            return jsonify(payload), 200

        last_status = status_code or 502
        last_payload = payload
        can_retry_model = (
            idx < len(models_to_try) - 1 and
            status_code in (400, 404) and
            model_not_found(payload)
        )
        if not can_retry_model:
            break

    error_message = parse_error_message(last_payload)
    return jsonify({
        'error': {
            'message': error_message,
            'model': requested_model,
            'statusCode': last_status,
        }
    }), (last_status or 502)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f'\nMirror Mirror running at http://localhost:{port}\n')
    app.run(host='0.0.0.0', port=port, debug=False)
