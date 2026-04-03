import requests
import os

models_dir = 'weights'
os.makedirs(models_dir, exist_ok=True)

base = 'https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights'

files = [
    'tiny_face_detector_model-weights_manifest.json',
    'tiny_face_detector_model-shard1',
    'face_expression_model-weights_manifest.json',
    'face_expression_model-shard1',
    'age_gender_model-weights_manifest.json',
    'age_gender_model-shard1',
]

for f in files:
    url = f'{base}/{f}'
    print(f'Downloading {f}...')
    r = requests.get(url, timeout=30)
    if r.status_code == 200:
        with open(f'{models_dir}/{f}', 'wb') as out:
            out.write(r.content)
        print(f'  OK ({len(r.content):,} bytes)')
    else:
        print(f'  FAILED {r.status_code}')

print('\nAll done! Run: python server.py')
