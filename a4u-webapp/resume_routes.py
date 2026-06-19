"""
resume_routes.py — 이력서 CRUD, 인증, 통계 API
Blueprint: /api
"""
import json
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, session
from models import db, User, Resume, ResumeTemplate, JobApplication, UploadedFile

resume_bp = Blueprint('resume_bp', __name__, url_prefix='/api')

# ─────────────────────────────────────────────
# 헬퍼
# ─────────────────────────────────────────────
def current_user():
    uid = session.get('user_id')
    if uid:
        return User.query.get(uid)
    return None

def login_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user():
            return jsonify(success=False, message='로그인이 필요합니다.'), 401
        return fn(*args, **kwargs)
    return wrapper

# ─────────────────────────────────────────────
# 인증 API
# ─────────────────────────────────────────────
@resume_bp.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not email or not password:
        return jsonify(success=False, message='이메일과 비밀번호를 입력해주세요.'), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify(success=False, message='이메일 또는 비밀번호가 올바르지 않습니다.'), 401

    if user.status != 'active':
        return jsonify(success=False, message='정지된 계정입니다. 관리자에게 문의하세요.'), 403

    session.permanent = True
    session['user_id'] = user.id
    session['user_name'] = user.name
    session['is_admin'] = user.is_admin
    return jsonify(success=True, user=user.to_dict())


@resume_bp.route('/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify(success=True, message='로그아웃 되었습니다.')


@resume_bp.route('/auth/me', methods=['GET'])
def me():
    user = current_user()
    if not user:
        return jsonify(success=False, message='로그인이 필요합니다.'), 401
    return jsonify(success=True, user=user.to_dict())


@resume_bp.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json(silent=True) or {}
    email = data.get('email', '').strip()
    name = data.get('name', '').strip()
    password = data.get('password', '')

    if not email or not name or not password:
        return jsonify(success=False, message='이름, 이메일, 비밀번호를 모두 입력해주세요.'), 400

    if User.query.filter_by(email=email).first():
        return jsonify(success=False, message='이미 등록된 이메일입니다.'), 409

    if len(password) < 6:
        return jsonify(success=False, message='비밀번호는 6자 이상이어야 합니다.'), 400

    user = User(email=email, name=name)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    session.permanent = True
    session['user_id'] = user.id
    session['user_name'] = user.name
    session['is_admin'] = user.is_admin
    return jsonify(success=True, user=user.to_dict()), 201


# ─────────────────────────────────────────────
# 이력서 CRUD API
# ─────────────────────────────────────────────
@resume_bp.route('/resumes', methods=['GET'])
def list_resumes():
    user = current_user()
    uid = user.id if user else None

    # 샘플은 항상 포함, 본인 이력서 포함
    if uid:
        resumes = Resume.query.filter(
            (Resume.user_id == uid) | (Resume.is_sample == True)
        ).order_by(Resume.created_at.desc()).all()
    else:
        resumes = Resume.query.filter_by(is_sample=True).all()

    return jsonify(success=True, resumes=[r.to_dict() for r in resumes])


@resume_bp.route('/resumes', methods=['POST'])
def create_resume():
    data = request.get_json(silent=True) or {}
    user = current_user()

    resume = Resume(
        user_id=user.id if user else None,
        template_id=data.get('template_id'),
        title=data.get('title', '새 이력서'),
        full_name=data.get('full_name', ''),
        email=data.get('email', ''),
        phone=data.get('phone', ''),
        location=data.get('location', ''),
        job_title=data.get('job_title', ''),
        summary=data.get('summary', ''),
        experience_json=json.dumps(data.get('experience', []), ensure_ascii=False),
        education_json=json.dumps(data.get('education', []), ensure_ascii=False),
        skills_json=json.dumps(data.get('skills', []), ensure_ascii=False),
        extra_json=json.dumps(data.get('extra', {}), ensure_ascii=False),
        sample_type=data.get('sample_type', 'custom'),
        is_sample=False,
    )
    db.session.add(resume)
    db.session.commit()
    return jsonify(success=True, resume=resume.to_dict()), 201


@resume_bp.route('/resumes/<int:resume_id>', methods=['GET'])
def get_resume(resume_id):
    resume = Resume.query.get_or_404(resume_id)
    user = current_user()
    # 샘플은 누구나 열람 가능, 본인 이력서만 접근
    if not resume.is_sample and (not user or resume.user_id != user.id):
        return jsonify(success=False, message='접근 권한이 없습니다.'), 403
    return jsonify(success=True, resume=resume.to_dict())


@resume_bp.route('/resumes/<int:resume_id>', methods=['PUT'])
@login_required
def update_resume(resume_id):
    resume = Resume.query.get_or_404(resume_id)
    user = current_user()
    if resume.is_sample:
        return jsonify(success=False, message='샘플 이력서는 수정할 수 없습니다.'), 403
    if resume.user_id != user.id:
        return jsonify(success=False, message='접근 권한이 없습니다.'), 403

    data = request.get_json(silent=True) or {}
    for field in ('title', 'full_name', 'email', 'phone', 'location', 'job_title', 'summary'):
        if field in data:
            setattr(resume, field, data[field])
    if 'experience' in data:
        resume.experience_json = json.dumps(data['experience'], ensure_ascii=False)
    if 'education' in data:
        resume.education_json = json.dumps(data['education'], ensure_ascii=False)
    if 'skills' in data:
        resume.skills_json = json.dumps(data['skills'], ensure_ascii=False)
    if 'extra' in data:
        resume.extra_json = json.dumps(data['extra'], ensure_ascii=False)
    if 'template_id' in data:
        resume.template_id = data['template_id']

    resume.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify(success=True, resume=resume.to_dict())


@resume_bp.route('/resumes/<int:resume_id>', methods=['DELETE'])
@login_required
def delete_resume(resume_id):
    resume = Resume.query.get_or_404(resume_id)
    user = current_user()
    if resume.is_sample:
        return jsonify(success=False, message='샘플 이력서는 삭제할 수 없습니다.'), 403
    if resume.user_id != user.id:
        return jsonify(success=False, message='접근 권한이 없습니다.'), 403
    db.session.delete(resume)
    db.session.commit()
    return jsonify(success=True, message='이력서가 삭제되었습니다.')


# ─────────────────────────────────────────────
# 제출 관리 API
# ─────────────────────────────────────────────
@resume_bp.route('/applications', methods=['GET'])
def list_applications():
    user = current_user()
    uid = user.id if user else None
    if uid:
        apps = JobApplication.query.filter_by(user_id=uid).order_by(JobApplication.created_at.desc()).all()
    else:
        apps = []
    return jsonify(success=True, applications=[a.to_dict() for a in apps])


@resume_bp.route('/applications', methods=['POST'])
def create_application():
    data = request.get_json(silent=True) or {}
    user = current_user()
    app_obj = JobApplication(
        user_id=user.id if user else None,
        resume_id=data.get('resume_id'),
        template_id=data.get('template_id'),
        company=data.get('company', ''),
        position=data.get('position', ''),
        status=data.get('status', 'draft'),
        notes=data.get('notes', ''),
    )
    db.session.add(app_obj)
    db.session.commit()
    return jsonify(success=True, application=app_obj.to_dict()), 201


@resume_bp.route('/applications/<int:app_id>', methods=['PUT'])
@login_required
def update_application(app_id):
    app_obj = JobApplication.query.get_or_404(app_id)
    user = current_user()
    if app_obj.user_id != user.id:
        return jsonify(success=False, message='접근 권한이 없습니다.'), 403
    data = request.get_json(silent=True) or {}
    for field in ('company', 'position', 'status', 'notes', 'template_id', 'resume_id'):
        if field in data:
            setattr(app_obj, field, data[field])
    if data.get('status') == 'submitted' and not app_obj.submitted_at:
        app_obj.submitted_at = datetime.now(timezone.utc)
    app_obj.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify(success=True, application=app_obj.to_dict())


# ─────────────────────────────────────────────
# 대시보드 통계 API
# ─────────────────────────────────────────────
@resume_bp.route('/stats', methods=['GET'])
def stats():
    total_users = User.query.filter_by(is_admin=False).count()
    total_resumes = Resume.query.filter_by(is_sample=False).count()
    total_uploads = UploadedFile.query.count()
    total_applications = JobApplication.query.count()
    submitted = JobApplication.query.filter_by(status='submitted').count()
    accepted = JobApplication.query.filter_by(status='accepted').count()

    sample_it = Resume.query.filter_by(is_sample=True, sample_type='it').count()
    sample_mgmt = Resume.query.filter_by(is_sample=True, sample_type='management').count()
    sample_general = Resume.query.filter_by(is_sample=True, sample_type='general').count()

    return jsonify(
        success=True,
        stats={
            'total_users': total_users,
            'total_resumes': total_resumes,
            'total_uploads': total_uploads,
            'total_applications': total_applications,
            'submitted_applications': submitted,
            'accepted_applications': accepted,
            'samples': {
                'it': sample_it,
                'management': sample_mgmt,
                'general': sample_general,
            }
        }
    )
