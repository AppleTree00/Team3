# API_BACKEND.md: 백엔드 에이전트 작업 지침

## 1. 목표

샘플 3종 기반 데이터 처리를 위한 Flask 서버 구축 및 AI 코칭 연동.

## 2. 주요 기능 및 구현 규칙

* **DB 스키마:** SQLite 사용. 샘플 3종에 맞춘 고정 스키마 및 확장 가능한 extra_json 필드 활용.
* **파일 업로드:** PDF/WORD 외 형식 업로드 시 400 에러와 함께 "지원하지 않는 파일 형식" 응답 반환.
* **AI 코칭:** 샘플 3종에 대한 Few-shot Prompting 적용. 샘플 이외의 케이스는 422 + 정중한 안내 메시지 반환.
* **통계/메모:** 단순 카운트 기반 대시보드 API 구현 (`GET /api/stats`).

## 3. 구현 완료 현황 (2026-06-19)

### DB 테이블 (SQLite, models.py)
| 테이블 | 상태 | 비고 |
|--------|------|------|
| users | ✅ 완료 | 이메일/비밀번호 인증 |
| resume_templates | ✅ 완료 | 3종 시드 (IT/경영/일반) |
| resumes | ✅ 완료 | 샘플 3종 시드, extra_json 확장 필드 |
| job_applications | ✅ 완료 | 제출 관리 |
| uploaded_files | ✅ 완료 | PDF/WORD 업로드 기록 |
| schema_migrations | ✅ 완료 | AI 스키마 콘솔용 |

### API 엔드포인트 (resume_routes.py)
| 엔드포인트 | 메서드 | 상태 |
|------------|--------|------|
| /api/auth/login | POST | ✅ |
| /api/auth/logout | POST | ✅ |
| /api/auth/me | GET | ✅ |
| /api/auth/register | POST | ✅ |
| /api/resumes | GET/POST | ✅ |
| /api/resumes/<id> | GET/PUT/DELETE | ✅ |
| /api/applications | GET/POST | ✅ |
| /api/applications/<id> | PUT | ✅ |
| /api/stats | GET | ✅ |

### AI 코칭 (coaching_routes.py)
| 엔드포인트 | 메서드 | 상태 |
|------------|--------|------|
| /api/coaching | POST | ✅ (Mock/OpenAI/Anthropic) |
| /api/coaching/samples | GET | ✅ |

### 지원 샘플 타입
| 타입 | 레이블 | Few-shot 예시 수 |
|------|--------|-----------------|
| it | IT 개발자형 | 2개 |
| management | 경영 관리자형 | 2개 |
| general | 일반 범용형 | 2개 |

### AI 연동 방식
1. `OPENAI_API_KEY` 환경변수 있으면 → GPT-4o-mini 사용
2. `ANTHROPIC_API_KEY` 있으면 → Claude-3-Haiku 사용
3. 둘 다 없으면 → Mock 피드백 반환 (시연용)

## 4. 3일차 마일스톤 달성 현황

* **1일차:** ✅ SQLite DB 테이블 생성 및 파일 업로드 API 구현
* **2일차:** ✅ AI 코칭 API 연결 (Few-shot 3종), 인증 API
* **3일차:** ✅ 통계 API 연동, QA 10종 시나리오 전부 통과

## 5. 테스트 계정
- 관리자: admin@a4u.com / admin1234
- 데모: demo@a4u.com / demo1234
