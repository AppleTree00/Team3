import json
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False, default='')
    is_admin = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    resumes = db.relationship('UploadedFile', backref='owner', lazy=True, foreign_keys='UploadedFile.user_id')
    resume_docs = db.relationship('Resume', backref='author', lazy=True, foreign_keys='Resume.user_id')
    applications = db.relationship('JobApplication', backref='applicant', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'is_admin': self.is_admin,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'resume_count': len(self.resumes)
        }


class ResumeTemplate(db.Model):
    __tablename__ = 'resume_templates'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50), default='general')
    html_content = db.Column(db.Text, nullable=False)
    thumbnail_url = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'html_content': self.html_content,
            'thumbnail_url': self.thumbnail_url,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Resume(db.Model):
    """구조화된 이력서 데이터 (샘플 3종 기반 고정 스키마 + extra_json 확장)"""
    __tablename__ = 'resumes'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    template_id = db.Column(db.Integer, db.ForeignKey('resume_templates.id'), nullable=True)
    title = db.Column(db.String(200), default='내 이력서')

    # 인적사항
    full_name = db.Column(db.String(100), default='')
    email = db.Column(db.String(255), default='')
    phone = db.Column(db.String(50), default='')
    location = db.Column(db.String(200), default='')
    job_title = db.Column(db.String(200), default='')

    # 자기소개 / 전문가 요약
    summary = db.Column(db.Text, default='')

    # 경력 (JSON 배열)
    # [{"company": "ABC", "position": "개발자", "start": "2020.03", "end": "현재", "bullets": ["..."]}, ...]
    experience_json = db.Column(db.Text, default='[]')

    # 학력 (JSON 배열)
    # [{"school": "한국대", "major": "컴퓨터공학", "start": "2014.03", "end": "2018.02", "degree": "학사"}]
    education_json = db.Column(db.Text, default='[]')

    # 기술 (JSON 배열)
    # ["Python", "Flask", "React", ...]
    skills_json = db.Column(db.Text, default='[]')

    # 확장 필드 (JSONB 대용)
    extra_json = db.Column(db.Text, default='{}')

    # 샘플 구분 (it / management / general / custom)
    sample_type = db.Column(db.String(50), default='custom')

    is_sample = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def get_experience(self):
        try:
            return json.loads(self.experience_json or '[]')
        except Exception:
            return []

    def get_education(self):
        try:
            return json.loads(self.education_json or '[]')
        except Exception:
            return []

    def get_skills(self):
        try:
            return json.loads(self.skills_json or '[]')
        except Exception:
            return []

    def get_extra(self):
        try:
            return json.loads(self.extra_json or '{}')
        except Exception:
            return {}

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'template_id': self.template_id,
            'title': self.title,
            'full_name': self.full_name,
            'email': self.email,
            'phone': self.phone,
            'location': self.location,
            'job_title': self.job_title,
            'summary': self.summary,
            'experience': self.get_experience(),
            'education': self.get_education(),
            'skills': self.get_skills(),
            'extra': self.get_extra(),
            'sample_type': self.sample_type,
            'is_sample': self.is_sample,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class JobApplication(db.Model):
    """제출 관리 — 지원처별 이력서 제출 기록"""
    __tablename__ = 'job_applications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    resume_id = db.Column(db.Integer, db.ForeignKey('resumes.id'), nullable=True)
    template_id = db.Column(db.Integer, db.ForeignKey('resume_templates.id'), nullable=True)

    company = db.Column(db.String(200), default='')
    position = db.Column(db.String(200), default='')
    # 상태: draft / submitted / reviewing / accepted / rejected
    status = db.Column(db.String(50), default='draft')
    notes = db.Column(db.Text, default='')
    submitted_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'resume_id': self.resume_id,
            'template_id': self.template_id,
            'company': self.company,
            'position': self.position,
            'status': self.status,
            'notes': self.notes,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class UploadedFile(db.Model):
    __tablename__ = 'uploaded_files'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    original_name = db.Column(db.String(255), nullable=False)
    saved_name = db.Column(db.String(255), nullable=False)
    size = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))
    uploaded_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    resume_analysis = db.Column(db.Text) # AI 코칭 결과 저장

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.owner.name if self.owner else '비회원',
            'original_name': self.original_name,
            'saved_name': self.saved_name,
            'size': self.size,
            'size_kb': round(self.size / 1024, 1) if self.size else 0,
            'mime_type': self.mime_type,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'resume_analysis': self.resume_analysis
        }


class SchemaMigration(db.Model):
    __tablename__ = 'schema_migrations'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text, nullable=False)
    natural_language = db.Column(db.Text)
    sql_query = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')
    error_message = db.Column(db.Text)
    applied_by = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    applied_at = db.Column(db.DateTime)

    def to_dict(self):
        return {
            'id': self.id,
            'description': self.description,
            'natural_language': self.natural_language,
            'sql_query': self.sql_query,
            'status': self.status,
            'error_message': self.error_message,
            'applied_by': self.applied_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'applied_at': self.applied_at.isoformat() if self.applied_at else None
        }
