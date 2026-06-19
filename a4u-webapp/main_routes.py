import os
import re
import time
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, redirect, send_from_directory, render_template, current_app
from .models import db, UploadedFile, ResumeTemplate

main_bp = Blueprint('main', __name__)

ALLOWED_MIMETYPES = {
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
}

def is_allowed_mimetype(mimetype):
    return mimetype in ALLOWED_MIMETYPES

# ── HTML 라우트 ────────────────────────────────────────────────
@main_bp.route('/')
def index():
    return redirect('/main.html')

@main_bp.route('/main.html')
def main_page():
    return render_template('main.html')

@main_bp.route('/admin.html')
def admin_page():
    return render_template('admin.html')

@main_bp.route('/dashboard.html')
def dashboard_page():
    return render_template('dashboard.html')

@main_bp.route('/builder.html')
def builder_page():
    return render_template('builder.html')

@main_bp.route('/profile-menu.html')
def profile_menu_page():
    return render_template('profile-menu.html')

@main_bp.route('/resume.html')
def resume_page():
    return render_template('resume.html')

@main_bp.route('/select.html')
def select_page():
    return render_template('select.html')

@main_bp.route('/timeline.html')
def timeline_page():
    return render_template('timeline.html')

@main_bp.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(current_app.root_path, '..'), 'favicon.svg', mimetype='image/svg+xml')

# ── API 라우트 ────────────────────────────────────────────────────
@main_bp.route('/api/admin/templates/<int:template_id>/preview')
def preview_template(template_id):
    t = ResumeTemplate.query.get_or_404(template_id)
    return t.html_content, 200, {'Content-Type': 'text/html; charset=utf-8'}

@main_bp.route('/upload-resume', methods=['POST'])
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
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        file_size = os.path.getsize(file_path)

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

@main_bp.route('/api/templates', methods=['GET'])
def public_templates():
    templates = ResumeTemplate.query.filter_by(is_active=True).all()
    return jsonify(templates=[t.to_dict() for t in templates])