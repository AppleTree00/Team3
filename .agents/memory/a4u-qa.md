---
name: a4u QA patterns
description: 검증된 예외처리 패턴 — 미구현 팝업, 파일업로드, 인증 가드
---

## 미구현 기능 처리 패턴
모든 HTML 페이지에 동일한 함수 삽입:
```javascript
function handleUnavailableFeature() {
    alert('현재 이 기능은 고도화 단계에 있습니다. 업데이트 이후 사용 가능하니 잠시만 기다려주세요.');
}
```
**Why:** PROJECT_MASTER.md 스펙 — 범위 외 기능은 반드시 이 메시지로 대체. 일관성 유지 필수.

## 파일 업로드 검증
- ALLOWED_MIMETYPES: application/pdf, application/msword, application/vnd.openxmlformats-officedocument.wordprocessingml.document
- 미지원 형식: 400 + "지원하지 않는 파일 형식입니다."
- 파일 없음: 400 + "파일이 필요합니다."

## 인증 가드
resume_routes.py의 `@login_required` 데코레이터 — session['user_id'] 없으면 401 반환.
샘플 이력서(is_sample=True)는 누구나 GET 가능, PUT/DELETE 불가.

## QA 통과 시나리오 (10종)
파일거부400, PDF허용200, 미인증401, IT코칭200, 경영코칭200, 일반코칭200, 미지원타입422, 통계200, 로그인200, 잘못된비번401.
