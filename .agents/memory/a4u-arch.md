---
name: a4u project architecture
description: Flask MVP 구조 — 블루프린트, DB 모델, 시드 데이터 배치 결정
---

## 블루프린트 구조
- `admin_bp` (admin_routes.py) — `/api/admin` 어드민 전용 15개 엔드포인트
- `resume_bp` (resume_routes.py) — `/api` 인증/이력서CRUD/제출/통계
- `coaching_bp` (coaching_routes.py) — `/api/coaching` AI 코칭

## DB 모델 (models.py)
6개 테이블: users, resume_templates, resumes, job_applications, uploaded_files, schema_migrations

**Why:** resumes 테이블은 구조화 필드(experience_json, education_json, skills_json) + extra_json 확장으로 샘플 3종 고정 스키마를 유지하면서 추후 확장 가능하게 설계.

## 시드 데이터
- admin@a4u.com / admin1234 (관리자)
- demo@a4u.com / demo1234 (데모 사용자)
- 샘플 이력서 3종: IT개발자(sample_type='it'), 경영관리자('management'), 일반범용('general')
- is_sample=True 플래그로 수정/삭제 보호

**How to apply:** init_db()에서 `Resume.query.filter_by(is_sample=True).count() == 0` 체크로 중복 시드 방지.

## AI 코칭 Fallback 순서
OpenAI(gpt-4o-mini) → Anthropic(claude-3-haiku) → Mock(항상 작동)
API 키 없어도 시연 가능한 Mock 응답 보장.
