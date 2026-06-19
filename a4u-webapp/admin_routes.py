import os
import json
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, session, current_app
from .models import db, User, ResumeTemplate, UploadedFile, SchemaMigration
from sqlalchemy import text, inspect

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin1234')

# ── 인증 ─────────────────────────────────────────────────────────────

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('is_admin'):
            return jsonify(success=False, message='인증이 필요합니다.'), 401
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    password = data.get('password', '')
    if password == ADMIN_PASSWORD:
        session['is_admin'] = True
        session.permanent = True
        return jsonify(success=True, message='로그인 성공')
    return jsonify(success=False, message='비밀번호가 올바르지 않습니다.'), 401


@admin_bp.route('/logout', methods=['POST'])
def admin_logout():
    session.pop('is_admin', None)
    return jsonify(success=True)


@admin_bp.route('/check', methods=['GET'])
def admin_check():
    return jsonify(authenticated=bool(session.get('is_admin')))


# ── 통계 ─────────────────────────────────────────────────────────────

@admin_bp.route('/stats', methods=['GET'])
@admin_required
def get_stats():
    total_users = User.query.count()
    active_users = User.query.filter_by(status='active').count()
    total_files = UploadedFile.query.count()
    total_templates = ResumeTemplate.query.filter_by(is_active=True).count()
    total_migrations = SchemaMigration.query.filter_by(status='applied').count()

    from sqlalchemy import func
    from datetime import timedelta
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    new_users_week = User.query.filter(User.created_at >= week_ago).count()
    new_files_week = UploadedFile.query.filter(UploadedFile.uploaded_at >= week_ago).count()

    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()

    return jsonify(
        total_users=total_users,
        active_users=active_users,
        total_files=total_files,
        total_templates=total_templates,
        total_migrations=total_migrations,
        new_users_week=new_users_week,
        new_files_week=new_files_week,
        recent_users=[u.to_dict() for u in recent_users]
    )


# ── 회원 관리 ─────────────────────────────────────────────────────────

@admin_bp.route('/users', methods=['GET'])
@admin_required
def list_users():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '')
    status_filter = request.args.get('status', '')

    query = User.query
    if search:
        query = query.filter(
            (User.name.ilike(f'%{search}%')) | (User.email.ilike(f'%{search}%'))
        )
    if status_filter:
        query = query.filter_by(status=status_filter)

    pagination = query.order_by(User.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    return jsonify(
        users=[u.to_dict() for u in pagination.items],
        total=pagination.total,
        pages=pagination.pages,
        current_page=page
    )


@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@admin_required
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())


@admin_bp.route('/users', methods=['POST'])
@admin_required
def create_user():
    data = request.get_json()
    if User.query.filter_by(email=data.get('email')).first():
        return jsonify(success=False, message='이미 사용 중인 이메일입니다.'), 400
    user = User(
        email=data.get('email'),
        name=data.get('name'),
        is_admin=data.get('is_admin', False),
        status=data.get('status', 'active')
    )
    user.set_password(data.get('password', 'changeme123'))
    db.session.add(user)
    db.session.commit()
    return jsonify(success=True, user=user.to_dict()), 201


@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    if 'name' in data:
        user.name = data['name']
    if 'email' in data:
        existing = User.query.filter_by(email=data['email']).first()
        if existing and existing.id != user_id:
            return jsonify(success=False, message='이미 사용 중인 이메일입니다.'), 400
        user.email = data['email']
    if 'status' in data:
        user.status = data['status']
    if 'is_admin' in data:
        user.is_admin = data['is_admin']
    if 'password' in data and data['password']:
        user.set_password(data['password'])
    user.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify(success=True, user=user.to_dict())


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify(success=True)


# ── 이력서 템플릿 관리 ────────────────────────────────────────────────

@admin_bp.route('/templates', methods=['GET'])
@admin_required
def list_templates():
    templates = ResumeTemplate.query.order_by(ResumeTemplate.created_at.desc()).all()
    return jsonify(templates=[t.to_dict() for t in templates])


@admin_bp.route('/templates/<int:template_id>', methods=['GET'])
@admin_required
def get_template(template_id):
    t = ResumeTemplate.query.get_or_404(template_id)
    return jsonify(t.to_dict())


@admin_bp.route('/templates', methods=['POST'])
@admin_required
def create_template():
    data = request.get_json()
    t = ResumeTemplate(
        name=data.get('name'),
        description=data.get('description', ''),
        category=data.get('category', 'general'),
        html_content=data.get('html_content', ''),
        thumbnail_url=data.get('thumbnail_url', ''),
        is_active=data.get('is_active', True)
    )
    db.session.add(t)
    db.session.commit()
    return jsonify(success=True, template=t.to_dict()), 201


@admin_bp.route('/templates/<int:template_id>', methods=['PUT'])
@admin_required
def update_template(template_id):
    t = ResumeTemplate.query.get_or_404(template_id)
    data = request.get_json()
    for field in ['name', 'description', 'category', 'html_content', 'thumbnail_url', 'is_active']:
        if field in data:
            setattr(t, field, data[field])
    t.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify(success=True, template=t.to_dict())


@admin_bp.route('/templates/<int:template_id>', methods=['DELETE'])
@admin_required
def delete_template(template_id):
    t = ResumeTemplate.query.get_or_404(template_id)
    db.session.delete(t)
    db.session.commit()
    return jsonify(success=True)


# ── 이력서 관리 ──────────────────────────────────────────────────────

@admin_bp.route('/resumes', methods=['GET'])
@admin_required
def list_all_resumes():
    from models import Resume
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '')
    sample_filter = request.args.get('is_sample', '')

    query = Resume.query
    if search:
        query = query.filter(Resume.title.ilike(f'%{search}%'))
    if sample_filter == 'true':
        query = query.filter_by(is_sample=True)
    elif sample_filter == 'false':
        query = query.filter_by(is_sample=False)

    pagination = query.order_by(Resume.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    resumes_data = []
    for r in pagination.items:
        d = r.to_dict()
        # 작성자 이름 추가
        if r.user_id:
            user = User.query.get(r.user_id)
            d['author_name'] = user.name if user else '알 수 없음'
        else:
            d['author_name'] = '시스템'
        resumes_data.append(d)

    return jsonify(
        resumes=resumes_data,
        total=pagination.total,
        pages=pagination.pages,
        current_page=page
    )


@admin_bp.route('/resumes/<int:resume_id>', methods=['DELETE'])
@admin_required
def delete_resume(resume_id):
    from models import Resume
    r = Resume.query.get_or_404(resume_id)
    if r.is_sample:
        return jsonify(success=False, message='샘플 이력서는 삭제할 수 없습니다.'), 400
    db.session.delete(r)
    db.session.commit()
    return jsonify(success=True)


# ── 파일 관리 ─────────────────────────────────────────────────────────

@admin_bp.route('/files', methods=['GET'])
@admin_required
def list_files():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '')

    query = UploadedFile.query
    if search:
        query = query.filter(UploadedFile.original_name.ilike(f'%{search}%'))

    pagination = query.order_by(UploadedFile.uploaded_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    return jsonify(
        files=[f.to_dict() for f in pagination.items],
        total=pagination.total,
        pages=pagination.pages,
        current_page=page
    )


@admin_bp.route('/files/<int:file_id>', methods=['DELETE'])
@admin_required
def delete_file(file_id):
    f = UploadedFile.query.get_or_404(file_id)
    upload_folder = current_app.config['UPLOAD_FOLDER']
    file_path = os.path.join(upload_folder, f.saved_name)
    if os.path.exists(file_path):
        os.remove(file_path)
    db.session.delete(f)
    db.session.commit()
    return jsonify(success=True)


# ── AI 스키마 콘솔 ────────────────────────────────────────────────────

@admin_bp.route('/schema/tables', methods=['GET'])
@admin_required
def get_schema():
    inspector = inspect(db.engine)
    tables = {}
    for table_name in inspector.get_table_names():
        columns = []
        for col in inspector.get_columns(table_name):
            columns.append({
                'name': col['name'],
                'type': str(col['type']),
                'nullable': col.get('nullable', True)
            })
        tables[table_name] = columns
    return jsonify(tables=tables)


@admin_bp.route('/schema/generate', methods=['POST'])
@admin_required
def generate_migration():
    data = request.get_json()
    natural_language = data.get('description', '')

    # AI 미연동 상태: 자연어 → SQL 변환 플레이스홀더
    # TODO: OpenAI / Claude API 키 설정 후 실제 AI 연동
    ai_available = bool(os.environ.get('OPENAI_API_KEY') or os.environ.get('ANTHROPIC_API_KEY'))

    if ai_available:
        sql = _call_ai_for_sql(natural_language)
    else:
        sql = _mock_sql_from_description(natural_language)

    return jsonify(
        success=True,
        natural_language=natural_language,
        suggested_sql=sql,
        ai_used=ai_available
    )


@admin_bp.route('/schema/apply', methods=['POST'])
@admin_required
def apply_migration():
    data = request.get_json()
    sql_query = data.get('sql_query', '').strip()
    description = data.get('description', '자동 마이그레이션')
    natural_language = data.get('natural_language', '')

    if not sql_query:
        return jsonify(success=False, message='SQL이 비어 있습니다.'), 400

    migration = SchemaMigration(
        description=description,
        natural_language=natural_language,
        sql_query=sql_query,
        applied_by='admin'
    )

    try:
        with db.engine.connect() as conn:
            for statement in sql_query.split(';'):
                stmt = statement.strip()
                if stmt:
                    conn.execute(text(stmt))
            conn.commit()
        migration.status = 'applied'
        migration.applied_at = datetime.now(timezone.utc)
        db.session.add(migration)
        db.session.commit()
        return jsonify(success=True, migration=migration.to_dict())
    except Exception as e:
        migration.status = 'failed'
        migration.error_message = str(e)
        db.session.add(migration)
        db.session.commit()
        return jsonify(success=False, message=str(e), migration=migration.to_dict()), 500


@admin_bp.route('/schema/migrations', methods=['GET'])
@admin_required
def list_migrations():
    migrations = SchemaMigration.query.order_by(SchemaMigration.created_at.desc()).limit(50).all()
    return jsonify(migrations=[m.to_dict() for m in migrations])


def _mock_sql_from_description(description: str) -> str:
    desc_lower = description.lower()
    if '컬럼' in description or 'column' in desc_lower or '추가' in description:
        return "-- AI 미연동 상태입니다. OPENAI_API_KEY 또는 ANTHROPIC_API_KEY 환경변수를 설정하세요.\n-- 예시:\nALTER TABLE users ADD COLUMN phone VARCHAR(20);"
    elif '테이블' in description or 'table' in desc_lower or '생성' in description:
        return "-- AI 미연동 상태입니다. OPENAI_API_KEY 또는 ANTHROPIC_API_KEY 환경변수를 설정하세요.\n-- 예시:\nCREATE TABLE new_table (\n  id INTEGER PRIMARY KEY AUTOINCREMENT,\n  name VARCHAR(100) NOT NULL,\n  created_at DATETIME DEFAULT CURRENT_TIMESTAMP\n);"
    elif '인덱스' in description or 'index' in desc_lower:
        return "-- AI 미연동 상태입니다. OPENAI_API_KEY 또는 ANTHROPIC_API_KEY 환경변수를 설정하세요.\n-- 예시:\nCREATE INDEX idx_users_email ON users(email);"
    else:
        return f"-- AI 미연동 상태입니다. OPENAI_API_KEY 또는 ANTHROPIC_API_KEY 환경변수를 설정하세요.\n-- 입력: {description}\n-- 여기에 SQL을 직접 작성하세요."


def _call_ai_for_sql(description: str) -> str:
    openai_key = os.environ.get('OPENAI_API_KEY')
    anthropic_key = os.environ.get('ANTHROPIC_API_KEY')

    inspector = inspect(db.engine)
    schema_info = {}
    for table_name in inspector.get_table_names():
        cols = [f"{c['name']} {c['type']}" for c in inspector.get_columns(table_name)]
        schema_info[table_name] = cols

    schema_str = json.dumps(schema_info, ensure_ascii=False, indent=2)
    prompt = f"""현재 SQLite 데이터베이스 스키마:
{schema_str}

다음 요청을 SQL DDL/DML 문으로 변환해주세요 (SQLite 문법 사용):
"{description}"

SQL만 반환하고 다른 설명은 생략하세요."""

    if openai_key:
        try:
            import openai
            client = openai.OpenAI(api_key=openai_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"-- OpenAI 오류: {e}"

    if anthropic_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=anthropic_key)
            message = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text.strip()
        except Exception as e:
            return f"-- Anthropic 오류: {e}"

    return _mock_sql_from_description(description)
