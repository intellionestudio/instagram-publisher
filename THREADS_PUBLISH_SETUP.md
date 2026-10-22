# Instagram + Threads 게시

전용 저장소: `intellionestudio/instagram-publisher`

1. Meta 앱 Carousel Workshop에 Threads API 이용 사례와 `threads_content_publish`를 추가합니다.
2. easyai_lab Threads 테스터 초대 수락 후 사용자 토큰 생성기로 장기 토큰을 발급합니다.
3. GitHub Actions Repository Secret에 `THREADS_ACCESS_TOKEN`을 저장합니다. Instagram Secret은 그대로 유지합니다.
4. 수동 `Check Threads connection` 작업은 프로필만 조회합니다. 게시 권한, 만료일 또는 실제 이미지 게시 성공까지 검증하는 작업은 아닙니다.
5. 최신 `publisher.py`, `.github/workflows/publish.yml`을 전용 저장소에 설치합니다. 과거 `queue/`, `state/`는 수정하거나 삭제하지 않습니다.
6. Workshop의 Instagram 게시 메뉴에서 게시 대상을 `Instagram + Threads`로 선택합니다. 기본값은 기존 동작인 Instagram만입니다.
7. Threads 문구는 캡션을 초기값으로 사용하되 사용자가 1~500자로 직접 편집합니다. 자동 축약, 삭제, 여러 글 분할은 하지 않습니다. Threads 문구는 현재 대기열 작업의 스냅샷에 저장되며 프로젝트 JSON 필드는 바꾸지 않습니다.
8. 같은 검증된 1080×1350 PNG에서 변환한 JPEG와 카드 순서를 두 플랫폼에 사용합니다. 즉시/예약 방식 모두 지원하며 처리 시각은 GitHub 실행 지연과 플랫폼 처리 속도에 따라 다릅니다.

## 안전과 상태

- 두 플랫폼 동시 게시는 원자적 트랜잭션이 아니라 같은 작업 내 순차 처리입니다.
- 플랫폼별 `queued → preparing → publishing → published` 상태를 `state/<job-id>.json`의 `platform_states`에 저장합니다.
- 모든 대상 성공은 `published`, 일부 성공 후 실패는 `partial_failure`, 결과가 불확실하면 `needs_review`입니다.
- 게시 호출 전에 GitHub에 플랫폼별 체크포인트를 저장합니다. 성공한 플랫폼이나 결과가 불확실한 플랫폼을 자동 재게시하지 않습니다.
- 기존 Instagram 전용 작업은 그대로 처리합니다. 이미 게시된 작업에 Threads를 소급해서 추가하지 않습니다.
- 문구/게시 대상/예약 시각을 바꾸면 새 작업이 됩니다. 실패 후 새 작업을 만들기 전에 실제 계정과 플랫폼별 상태를 확인하세요.
- 댓글/DM 자동 응답과 토큰 자동 갱신은 이 기능에 포함되지 않습니다.

공식 구현 참고: https://github.com/fbsamples/threads_api/tree/main/postman
