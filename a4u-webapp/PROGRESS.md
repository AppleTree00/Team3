# 작업 진행 현황 (자동 관리 파일)

> 최종 업데이트: 2026-06-19

## 완료된 작업

### [T001] DB 스키마 확장 ✅
- `models.py` — Resume, JobApplication 모델 추가 (샘플 3종 고정 스키마 + extra_json 확장 필드)
- 샘플 이력서 3종 시드: IT 개발자형(김개발), 경영 관리자형(이매니저), 일반 범용형(박지원)
- 데모 계정 추가: demo@a4u.com / demo1234

### [T002] 핵심 API 엔드포인트 ✅
- `resume_routes.py` 신규 생성 (Blueprint: /api)
  - POST /api/auth/login — 이메일/비밀번호 세션 로그인
  - GET  /api/auth/me — 현재 사용자 조회
  - POST /api/auth/logout — 로그아웃
  - POST /api/auth/register — 신규 가입
  - GET  /api/resumes — 이력서 목록 (샘플 + 본인)
  - POST /api/resumes — 이력서 생성
  - GET  /api/resumes/<id> — 이력서 조회
  - PUT  /api/resumes/<id> — 이력서 수정 (인증 필요)
  - DELETE /api/resumes/<id> — 이력서 삭제 (인증 필요)
  - GET  /api/applications — 제출 목록
  - POST /api/applications — 제출 생성
  - PUT  /api/applications/<id> — 제출 수정
  - GET  /api/stats — 대시보드 통계

### [T003] AI 코칭 API ✅
- `coaching_routes.py` 신규 생성
  - POST /api/coaching — Few-shot 3종 프롬프트 기반 코칭
  - GET  /api/coaching/samples — 지원 가능한 샘플 타입 목록
  - OpenAI(gpt-4o-mini) → Anthropic(claude-3-haiku) → Mock 순서로 Fallback
  - 미지원 타입: 422 + "고도화 단계" 안내 메시지

### [T004] 프론트엔드 팝업 + API 연동 ✅
- 전체 6개 페이지에 `handleUnavailableFeature()` 적용:
  - main.html, dashboard.html, builder.html, resume.html, timeline.html, profile-menu.html
- dashboard.html: /api/stats 실시간 연동, 버튼별 동작 연결
- builder.html: /api/resumes 저장 연동, /api/coaching AI 코칭 연동
- profile-menu.html: 로그아웃 → /api/auth/logout, 나머지 메뉴 팝업
- resume.html: /api/resumes 목록 연동, 인쇄 버튼 동작

### [T005] QA 점검 ✅ (10/10 PASS)
| 시나리오 | 결과 |
|----------|------|
| 지원하지 않는 파일 형식 업로드 → 400 | PASS |
| PDF 파일 업로드 → 200 | PASS |
| 인증 없이 이력서 수정 → 401 | PASS |
| AI 코칭 샘플 3종(it/management/general) → 200 | PASS |
| AI 코칭 미지원 타입 → 422 + 안내 메시지 | PASS |
| 통계 API → 200 | PASS |
| 이력서 목록 샘플 3종 확인 | PASS |
| demo 로그인 → 200 | PASS |
| 잘못된 비밀번호 → 401 | PASS |
| 코칭 빈 텍스트 → 400 | PASS |

## 미구현 / 업데이트 예정
- Google OAuth 로그인 (현재: 이메일/비밀번호 세션 방식)
- 이력서 PDF 다운로드 (현재: 팝업 안내)
- 드래그앤드롭 캔반 보드 (현재: UI만 표시)
- 커리어 타임라인 일정 추가 (현재: 팝업 안내)
- 포트폴리오/경력관리 메뉴 (현재: 팝업 안내)

## 계정 정보
| 계정 | 이메일 | 비밀번호 | 권한 |
|------|--------|----------|------|
| 관리자 | admin@a4u.com | admin1234 | 어드민 |
| 데모 | demo@a4u.com | demo1234 | 일반 |

## 주요 파일
| 파일 | 역할 |
|------|------|
| app.py | Flask 앱 진입점, DB 초기화, 블루프린트 등록 |
| models.py | SQLAlchemy 모델 (User, Resume, JobApplication, ResumeTemplate, UploadedFile, SchemaMigration) |
| resume_routes.py | 인증 + 이력서 CRUD + 통계 API |
| coaching_routes.py | AI 코칭 API (Few-shot 3종) |
| admin_routes.py | 어드민 대시보드 API |
| admin.html | 어드민 대시보드 UI |
