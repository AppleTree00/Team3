import os
import re
import time
from datetime import datetime, timezone, timedelta
from flask import Flask, request, jsonify, redirect, send_from_directory
from flask_cors import CORS
from werkzeug.exceptions import RequestEntityTooLarge, HTTPException
from models import db, User, UploadedFile

app = Flask(__name__, static_folder='.', static_url_path='')
app.secret_key = os.environ.get('SECRET_KEY', 'a4u-dev-secret-key-change-in-production')
app.permanent_session_lifetime = timedelta(hours=8)

CORS(app)

# ── DB 설정 ───────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(BASE_DIR, 'a4u.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# ── 어드민 블루프린트 등록 ─────────────────────────────────────────────
from admin_routes import admin_bp
app.register_blueprint(admin_bp)

# ── 어드민 HTML 라우트 ────────────────────────────────────────────────
@app.route('/admin')
@app.route('/admin.html')
def admin_page():
    return send_from_directory(BASE_DIR, 'admin.html')

# ── 템플릿 미리보기 ────────────────────────────────────────────────────
@app.route('/api/admin/templates/<int:template_id>/preview')
def preview_template(template_id):
    from models import ResumeTemplate
    t = ResumeTemplate.query.get_or_404(template_id)
    return t.html_content, 200, {'Content-Type': 'text/html; charset=utf-8'}

# ── 서버 설정 ─────────────────────────────────────────────────────────
PORT = os.environ.get('PORT', 5000)
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024
ALLOWED_MIMETYPES = {
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def is_allowed_mimetype(mimetype):
    return mimetype in ALLOWED_MIMETYPES

# ── 기존 라우트 ───────────────────────────────────────────────────────
@app.route('/')
def index():
    return redirect('/main.html')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(BASE_DIR, 'favicon.svg', mimetype='image/svg+xml')

@app.route('/upload-resume', methods=['POST'])
def upload_resume():
    if 'resumeFile' not in request.files:
        return jsonify(success=False, message='파일이 필요합니다.'), 400

    file = request.files['resumeFile']
    if file.filename == '':
        return jsonify(success=False, message='파일이 선택되지 않았습니다.'), 400

    if file and is_allowed_mimetype(file.mimetype):
        sanitized_original = re.sub(r'[^a-zA-Z0-9._-]', '-', file.filename)
        timestamp = int(time.time() * 1000)
        filename = f"{timestamp}-{sanitized_original}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        file_size = os.path.getsize(file_path)

        # DB에 파일 정보 저장
        uploaded = UploadedFile(
            original_name=file.filename,
            saved_name=filename,
            size=file_size,
            mime_type=file.mimetype
        )
        db.session.add(uploaded)
        db.session.commit()

        return jsonify({
            "success": True,
            "originalName": file.filename,
            "savedName": filename,
            "size": file_size,
            "mimeType": file.mimetype,
            "uploadedAt": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        })
    else:
        return jsonify(success=False, message='PDF, DOC, DOCX 파일만 업로드할 수 있습니다.'), 400

# ── 이력서 템플릿 공개 API (프론트에서 사용) ──────────────────────────
@app.route('/api/templates', methods=['GET'])
def public_templates():
    from models import ResumeTemplate
    templates = ResumeTemplate.query.filter_by(is_active=True).all()
    return jsonify(templates=[t.to_dict() for t in templates])

# ── 오류 핸들러 ───────────────────────────────────────────────────────
@app.errorhandler(413)
@app.errorhandler(RequestEntityTooLarge)
def handle_too_large(e):
    return jsonify(success=False, message=f'파일 크기는 {app.config["MAX_CONTENT_LENGTH"] / 1024 / 1024:.0f}MB를 초과할 수 없습니다.'), 413

@app.errorhandler(Exception)
def handle_exception(e):
    if isinstance(e, HTTPException):
        return e
    print(f"An error occurred: {e}")
    return jsonify(success=False, message='알 수 없는 오류가 발생했습니다.'), 500

# ── DB 초기화 및 시드 데이터 ─────────────────────────────────────────
def init_db():
    with app.app_context():
        db.create_all()
        # 기본 관리자 계정 생성 (없으면)
        if not User.query.filter_by(email='admin@a4u.com').first():
            admin = User(
                email='admin@a4u.com',
                name='관리자',
                is_admin=True,
                status='active'
            )
            admin.set_password(os.environ.get('ADMIN_PASSWORD', 'admin1234'))
            db.session.add(admin)

        # 기본 이력서 템플릿 (없으면)
        from models import ResumeTemplate
        if ResumeTemplate.query.count() == 0:
            seed_templates = [
                ResumeTemplate(
                    name='IT 개발자형',
                    description='소프트웨어 개발자를 위한 기술 스택 중심 이력서',
                    category='it',
                    html_content=_default_template('IT 개발자형'),
                    is_active=True
                ),
                ResumeTemplate(
                    name='경영 관리자형',
                    description='프로젝트 관리 및 리더십 경험을 강조한 이력서',
                    category='management',
                    html_content=_default_template('경영 관리자형'),
                    is_active=True
                ),
                ResumeTemplate(
                    name='일반 범용형',
                    description='다양한 직군에 활용 가능한 기본 이력서 템플릿',
                    category='general',
                    html_content=_default_template('일반 범용형'),
                    is_active=True
                ),
            ]
            for t in seed_templates:
                db.session.add(t)

        db.session.commit()
        print("DB initialized.")

def _default_template(name):
    return f"""<!DOCTYPE html>
<html lang="ko">
<head><meta charset="utf-8"/><title>{name} 이력서</title>
<style>
body {{ font-family: 'Inter', sans-serif; max-width: 800px; margin: 40px auto; padding: 0 24px; color: #111c2d; }}
h1 {{ color: #3525cd; font-size: 28px; margin-bottom: 4px; }}
.section {{ margin-top: 28px; border-top: 2px solid #e7eeff; padding-top: 16px; }}
.section h2 {{ color: #3525cd; font-size: 14px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 12px; }}
.item {{ margin-bottom: 16px; }}
.item-title {{ font-weight: 600; }}
.item-sub {{ color: #6b7280; font-size: 14px; }}
</style>
</head>
<body>
<h1>홍길동</h1>
<p style="color:#6b7280;font-size:14px;">hong@example.com · 010-0000-0000 · 서울시</p>
<div class="section">
  <h2>경력</h2>
  <div class="item">
    <div class="item-title">시니어 개발자 — ABC 회사</div>
    <div class="item-sub">2020.03 ~ 현재</div>
    <ul style="font-size:14px;margin-top:6px;padding-left:18px;color:#374151;">
      <li>주요 업무 내용을 여기에 작성합니다.</li>
    </ul>
  </div>
</div>
<div class="section">
  <h2>학력</h2>
  <div class="item">
    <div class="item-title">한국대학교 컴퓨터공학과</div>
    <div class="item-sub">2014.03 ~ 2018.02 졸업</div>
  </div>
</div>
<div class="section">
  <h2>기술</h2>
  <p style="font-size:14px;">Python, Flask, SQL, JavaScript, React</p>
</div>
</body>
</html>"""

if __name__ == '__main__':
    init_db()
    print(f"Server is running at http://localhost:{PORT}")
    print(f"Admin console: http://localhost:{PORT}/admin")
    app.run(host='0.0.0.0', port=int(PORT), debug=True)
