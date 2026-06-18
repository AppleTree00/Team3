# GitHub Pages 배포 가이드

## 1. 압축 해제

ZIP 파일을 압축 해제합니다.

## 2. 로컬에서 먼저 확인

`index.html`을 더블클릭합니다. 외부 API가 차단되는 환경이면 다음 명령으로 로컬 서버를 실행합니다.

```bash
python -m http.server 8000
```

브라우저에서 `http://localhost:8000`으로 접속합니다.

## 3. GitHub Desktop 업로드

1. GitHub Desktop 실행
2. File → Add local repository
3. 압축 해제한 폴더 선택
4. Commit to main
5. Publish repository

## 4. GitHub Pages 설정

1. GitHub 웹에서 저장소 열기
2. Settings → Pages
3. Source: Deploy from a branch
4. Branch: main
5. Folder: /root
6. Save

## 5. 팀원 공유

GitHub가 생성한 Pages URL을 공유합니다.

## 오류가 보일 때

- `file://`에서 API가 실패하면 `python -m http.server 8000`로 확인합니다.
- 회사망, 보안 프로그램, 브라우저 확장 프로그램이 외부 API를 막을 수 있습니다.
- 자동 안정 모드는 GDELT → HN → Spaceflight 순서로 재시도합니다.
