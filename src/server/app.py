from flask import Flask, send_file, send_from_directory, abort, Response
from pathlib import Path
import zstandard as zstd

app = Flask(__name__)

# === 경로 설정 ===
PROJECT_ROOT = Path(__file__).resolve().parents[2]
VISUALIZER_DIR = PROJECT_ROOT / 'src' / 'visualizer'
LOGS_DIR = PROJECT_ROOT / 'logs'
LOGS_COMPRESSED_DIR = LOGS_DIR / 'compressed'

# === 유틸 함수 ===
def abort_with_log(status_code, message):
    print(message)
    abort(status_code, description=message)

def serve_file_safe(path: Path, mimetype=None):
    if not path.is_file():
        abort_with_log(404, f"파일을 찾을 수 없습니다: {path}")
    return send_file(str(path), mimetype=mimetype)

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

@app.route('/logs/<path:filename>')
def raw_logs(filename):
    return serve_file_safe(LOGS_DIR / filename)

# === 실행 ===
if __name__ == '__main__':
    app.run(debug=True, port=5000)
