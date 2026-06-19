# UI_FRONTEND.md: 프론트엔드 에이전트 작업 지침

## 1. 목표

샘플 이력서 3종에 최적화된 2종의 고정 템플릿 UI 구현 및 사용자 인터랙션 처리.

## 2. 주요 기능 및 구현 규칙

* **UI 템플릿:** 기획된 2종 레이아웃을 HTML/CSS(Tailwind)로 고정 구현.
* **입력 폼 제한:** 샘플 데이터의 필드와 일치하지 않는 입력 시 안내.
* **미구현 기능 호출:** 모든 미구현 버튼/기능에 대해 다음 함수를 호출하여 팝업 처리.

```javascript
function handleUnavailableFeature() {
    alert("현재 이 기능은 고도화 단계에 있습니다. 업데이트 이후 사용 가능하니 잠시만 기다려주세요.");
}
```

## 3. 구현 완료 현황 (2026-06-19)

### 페이지별 상태
| 페이지 | 상태 | 주요 기능 |
|--------|------|-----------|
| main.html | ✅ 완료 | 알림 팝업, 풋터 링크 팝업 |
| dashboard.html | ✅ 완료 | /api/stats 연동, 버튼 팝업, 이력서 작성 이동 |
| builder.html | ✅ 완료 | /api/resumes 저장, /api/coaching AI 코칭 |
| resume.html | ✅ 완료 | /api/resumes 목록 연동, 인쇄 연동 |
| select.html | ✅ 완료 | 파일 업로드 null guard 적용 |
| timeline.html | ✅ 완료 | 일정 버튼 팝업, 알림 팝업 |
| profile-menu.html | ✅ 완료 | 로그아웃 → /api/auth/logout, 메뉴 팝업 |
| admin.html | ✅ 완료 | 어드민 대시보드 (5개 섹션) |

### handleUnavailableFeature() 적용 범위
| 기능 | 페이지 | 처리 방식 |
|------|--------|-----------|
| 알림(notifications) 버튼 | 전체 | 팝업 |
| 풋터 링크 (소개, 약관 등) | 전체 | 팝업 |
| Google 로그인 | main.html | 팝업 |
| 프로필 정보 업데이트 | dashboard.html | 팝업 |
| 지원 필터/새로 추가 | dashboard.html | 팝업 |
| 일정 추가/내보내기 | timeline.html | 팝업 |
| 계정 메뉴 (개인정보, 보안 등) | profile-menu.html | 팝업 |
| 계정 삭제 | profile-menu.html | 팝업 |
| PDF 다운로드/공유 | resume.html, builder.html | 팝업 |

### 구현된 실제 기능 (팝업 아님)
| 기능 | 페이지 | 연동 |
|------|--------|------|
| 새 이력서 작성 | dashboard.html | → builder.html 이동 |
| 이력서 보완하기 | dashboard.html | → builder.html 이동 |
| 이력서 저장 | builder.html | POST /api/resumes |
| AI 코칭 | builder.html | POST /api/coaching |
| 인쇄 | builder.html, resume.html | window.print() |
| 로그아웃 | profile-menu.html | POST /api/auth/logout |
| 통계 수치 | profile-menu.html | GET /api/stats |

## 4. 3일차 마일스톤 달성 현황

* **1일차:** ✅ 로그인 화면 및 기본 이력서 작성 폼 구조 설계
* **2일차:** ✅ 이력서/지원처 미리보기 화면, AI 코칭 대화창 레이아웃
* **3일차:** ✅ 전체 페이지 인터랙션 점검, 미구현 기능 팝업 연결 확인
