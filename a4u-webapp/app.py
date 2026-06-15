import os
import re
import time
from datetime import datetime, timezone
from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
from werkzeug.exceptions import RequestEntityTooLarge

# 프로젝트 루트 디렉토리를 기준으로 static 폴더를 설정하여
# 현재 디렉토리('.')를 정적 파일 폴더로 사용하고, URL 경로를 루트('')로 설정합니다.
# 이렇게 하면 main.html, select.html 등을 http://localhost:3000/main.html 처럼 직접 접근할 수 있습니다.
app = Flask(__name__, static_folder='.', static_url_path='')

# CORS 설정
CORS(app)

@app.route('/')
def index():
    """웹사이트의 첫 페이지로 접근 시 /main.html로 리디렉션합니다."""
    return redirect('/main.html')

# 서버 설정
PORT = os.environ.get('PORT', 3000)
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB 파일 크기 제한
ALLOWED_MIMETYPES = {
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
}

# 'uploads' 폴더가 없으면 생성합니다.
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def is_allowed_mimetype(mimetype):
    """허용된 MIME 타입인지 확인합니다."""
    return mimetype in ALLOWED_MIMETYPES

@app.route('/upload-resume', methods=['POST'])
def upload_resume():
    """이력서 파일 업로드 처리 라우트"""
    if 'resumeFile' not in request.files:
        return jsonify(success=False, message='파일이 필요합니다.'), 400

    file = request.files['resumeFile']

    if file.filename == '':
        return jsonify(success=False, message='파일이 선택되지 않았습니다.'), 400

    if file and is_allowed_mimetype(file.mimetype):
        # server.js와 동일한 방식으로 파일 이름을 생성합니다.
        # 1. 원본 파일명에서 안전하지 않은 문자 제거
        sanitized_original = re.sub(r'[^a-zA-Z0-9._-]', '-', file.filename)
        # 2. 타임스탬프와 결합
        timestamp = int(time.time() * 1000)
        filename = f"{timestamp}-{sanitized_original}"
        
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        file_size = os.path.getsize(file_path)

        # server.js의 응답 형식과 동일하게 구성
        response_data = {
            "success": True,
            "originalName": file.filename,
            "savedName": filename,
            "size": file_size,
            "mimeType": file.mimetype,
            "uploadedAt": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        }
        return jsonify(response_data)
    else:
        return jsonify(success=False, message='PDF, DOC, DOCX 파일만 업로드할 수 있습니다.'), 400

# 오류 핸들러
@app.errorhandler(413)
@app.errorhandler(RequestEntityTooLarge)
def handle_request_entity_too_large(e):
    """파일 크기 초과 오류를 처리합니다."""
    return jsonify(success=False, message=f'파일 크기는 {app.config["MAX_CONTENT_LENGTH"] / 1024 / 1024:.0f}MB를 초과할 수 없습니다.'), 413

@app.errorhandler(Exception)
def handle_generic_exception(e):
    """그 외 모든 예외를 처리합니다."""
    # 운영 환경에서는 오류 로깅이 필요합니다.
    print(f"An error occurred: {e}")
    return jsonify(success=False, message='알 수 없는 오류가 발생했습니다.'), 500

# Flask 앱 실행
if __name__ == '__main__':
    print(f"Server is running at http://localhost:{PORT}")
    # server.js의 로그 메시지와 동일하게 출력
    print('Open /select.html to test resume upload.')
    app.run(host='0.0.0.0', port=PORT, debug=True)