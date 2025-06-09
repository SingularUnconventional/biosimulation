import sys
import os

# 현재 파일 기준으로 상위 폴더 경로 계산
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(parent_dir)


from src.entities.genome import Genome
from src.utils.trait_computer import compute_biological_traits

from flask import Flask, jsonify, send_file, send_from_directory, abort, Response
from pathlib import Path
from dataclasses import asdict
import zstandard as zstd
import numpy as np
import json
import base64
import io
import zipfile


app = Flask(__name__)

# === 경로 설정 ===
PROJECT_ROOT = Path(__file__).resolve().parents[2]
VISUALIZER_DIR = PROJECT_ROOT / 'src' / 'visualizer'
LOGS_DIR = PROJECT_ROOT / 'logs'
LOGS_COMPRESSED_DIR = LOGS_DIR / 'compressed'
GENETIC_DATA_PATH = LOGS_DIR / "static_data.jsonl"
OFFSET_INDEX_PATH = LOGS_DIR / "offsets.bin"
CREATURE_SHEET_PATH = LOGS_DIR / "creature_sheet.png"


# === 유틸 함수 ===
def abort_with_log(status_code, message):
    print(message)
    abort(status_code, description=message)

def serve_file_safe(path: Path, mimetype=None):
    if not path.is_file():
        abort_with_log(404, f"파일을 찾을 수 없습니다: {path}")
    return send_file(str(path), mimetype=mimetype)

def load_offset_index():
    try:
        with open(OFFSET_INDEX_PATH, "rb") as f:
            data = f.read()
            return [int.from_bytes(data[i:i+8], "little") for i in range(0, len(data), 8)]
    except FileNotFoundError:
        print("❌ offsets.bin 파일이 존재하지 않습니다.")
        return []


def convert_ndarray_and_set(obj):
    if isinstance(obj, dict):
        return {
            k: convert_ndarray_and_set(v)
            for k, v in obj.items()
        }
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, set):
        return list(obj)
    else:
        return obj


# === 라우터 ===
@app.route('/')
def index():
    return serve_file_safe(VISUALIZER_DIR / 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    return serve_file_safe(VISUALIZER_DIR / filename)

@app.route('/logs/compressed/<path:filename>')
def compressed_logs(filename):
    file_path = LOGS_COMPRESSED_DIR / filename

    if filename.endswith('.jsonl'):
        return serve_file_safe(file_path)

    elif filename.endswith('.zst'):
        if not file_path.is_file():
            abort_with_log(404, f"압축 로그 파일이 존재하지 않습니다: {file_path}")
        try:
            with open(file_path, 'rb') as f:
                dctx = zstd.ZstdDecompressor()
                decompressed = dctx.decompress(f.read())
            return Response(decompressed, content_type='application/json')
        except Exception as e:
            abort_with_log(500, f"압축 해제 실패: {e}")

    abort_with_log(400, f"지원하지 않는 파일 유형입니다: {filename}")

@app.route('/logs/<int:object_id>')
def serve_gene(object_id):
    global offset_index
    if object_id >= len(offset_index):
        offset_index = load_offset_index()
        abort_with_log(404, f"ID {object_id}에 해당하는 유전자 정보가 존재하지 않습니다.")
    try:
        offset = offset_index[object_id]
        with open(GENETIC_DATA_PATH, "rb") as f:
            f.seek(offset)
            line = f.readline().decode("utf-8").strip()
            raw_bytes = base64.b64decode(line)
            interpreted = asdict(compute_biological_traits(Genome(raw_bytes).traits))
            interpreted = convert_ndarray_and_set(interpreted)
            return jsonify(interpreted)
    except Exception as e:
        abort_with_log(500, f"유전자 처리 중 오류 발생: {e}")

@app.route("/logs/sheet")
def serve_zipped_creature_sheet():
    try:
        if not os.path.exists(CREATURE_SHEET_PATH):
            abort_with_log(404, "시트 이미지가 존재하지 않습니다.")

        # ZIP 버퍼 생성
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(CREATURE_SHEET_PATH, arcname="creature_sheet.png")

        zip_buffer.seek(0)
        return send_file(
            zip_buffer,
            mimetype="application/zip",
            as_attachment=True,
            download_name="creature_sheet.zip"
        )
    except Exception as e:
        abort_with_log(500, f"시트 압축 중 오류 발생: {e}")

@app.route('/logs/<path:filename>')
def raw_logs(filename):
    return serve_file_safe(LOGS_DIR / filename)

# === 실행 ===
if __name__ == '__main__':
    offset_index = load_offset_index()
    app.run(debug=True, port=5000)
