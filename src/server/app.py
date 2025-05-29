from flask import Flask, send_file, send_from_directory, abort, Response
import os
import zstandard as zstd
import gzip
import io

app = Flask(__name__)

# 경로 설정
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
TEST_DIR = os.path.join(PROJECT_ROOT, 'src/visualizer')
LOGS_DIR = os.path.join(PROJECT_ROOT, 'logs')
LOGS_COMPRESSED_DIR = os.path.join(LOGS_DIR, 'compressed')

# index.html 반환
@app.route('/')
def serve_index():
    try:
        return send_file(os.path.join(TEST_DIR, 'index.html'))
    except Exception as e:
        print("Error serving index.html:", e)
        abort(500)

# test 폴더의 정적 파일 제공 (style.css, script.js 등)
@app.route('/<path:filename>')
def serve_static_file(filename):
    try:
        return send_from_directory(TEST_DIR, filename)
    except Exception as e:
        print(f"Error serving file '{filename}':", e)
        abort(500)

# logs/compressed/zst 파일 요청 시 GZIP 압축 응답
@app.route('/logs/compressed/<path:filename>')
def serve_compressed(filename):
    file_path = os.path.join(LOGS_COMPRESSED_DIR, filename)

    # ✅ 일반 파일 (예: index.jsonl)은 압축 해제 없이 그대로 제공
    if filename.endswith('.jsonl'):
        if not os.path.isfile(file_path):
            abort(404)
        return send_from_directory(LOGS_COMPRESSED_DIR, filename)

    # ✅ .zst 파일은 해제 후 GZIP 압축 전송
    if filename.endswith('.zst'):
        if not os.path.isfile(file_path):
            abort(404, description="압축 로그 파일이 존재하지 않습니다.")

        try:
            with open(file_path, 'rb') as f:
                dctx = zstd.ZstdDecompressor()
                decompressed = dctx.decompress(f.read())

            return Response(decompressed, content_type='application/json')

        except Exception as e:
            print(f"압축 해제 실패: {e}")
            abort(500, description="Zstandard → GZIP 변환 실패")

    abort(400, description="지원하지 않는 파일 유형입니다.")

# logs 폴더의 그 외 정적 파일 제공
@app.route('/logs/<path:filename>')
def serve_logs(filename):
    try:
        return send_from_directory(LOGS_DIR, filename)
    except Exception as e:
        print(f"Error serving logs file '{filename}':", e)
        abort(500)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
