# 개인용 Instagram 게시 연결

Carousel Workshop 상단의 **Instagram 게시**를 누른 뒤 **GitHub 연결 설정**을
열고 **GitHub 게시 서버 설치 파일 받기**로 ZIP을 내려받으세요.

## 1. 전용 GitHub 저장소

- 새 저장소를 만들고 ZIP 안의 파일 전체를 기본 브랜치 `main`에 올립니다.
  숨김 폴더 `.github/workflows/publish.yml`도 반드시 포함해야 합니다.
- 현재 작업 폴더 전체를 올리지 마세요. 설치 ZIP과 전송할 게시물만 사용합니다.
- 저장소 Settings → Pages → Source를 **GitHub Actions**로 선택합니다.
- GitHub Free에서 Pages를 사용하려면 공개 저장소로 시작할 수 있습니다.
  이 경우 이미지와 게시 메타데이터 모두 저장소에서 공개됩니다.

## 2. Meta 계정 연결

Instagram Business 또는 Creator 계정으로 Meta 개발자 앱에서 Instagram Login을
구성하고 게시 권한을 가진 액세스 토큰을 발급합니다.
필요한 권한은 `instagram_business_basic`, `instagram_business_content_publish`입니다.
발급 과정의 정확한 요구 조건은 Meta 개발자 대시보드 안내를 따르세요.

GitHub 저장소 Settings → Secrets and variables → Actions → Secrets에 저장:

- `INSTAGRAM_ACCOUNT_ID`: 게시 대상 계정 ID
- `INSTAGRAM_ACCESS_TOKEN`: 해당 계정에 게시할 수 있는 토큰

같은 화면의 Variables에 저장:

- `PAGES_BASE_URL`: Pages 사이트 HTTPS 주소, 끝의 `/` 제외
- `INSTAGRAM_API_VERSION`: Meta 앱에서 지원하는 Graph API 버전 (`v숫자.숫자`)
- `INSTAGRAM_GRAPH_HOST`: Instagram Login이면 `graph.instagram.com`

Facebook Login 경로를 사용하면 `graph.facebook.com`과 해당 인증 경로의 토큰·권한을
사용해야 합니다. 두 경로의 토큰을 섞지 않습니다.
액세스 토큰이 만료되면 Secrets를 갱신해야 합니다.

## 3. 로컬 서버의 GitHub 연결

전용 저장소에만 접근할 수 있는 fine-grained GitHub 토큰을 만들고
Contents 권한을 Read and write로 설정합니다. 설치 파일을 직접 올리므로
워크플로 수정 권한은 필요하지 않습니다.

로컬 서버를 실행하는 터미널 환경에 `WORKSHOP_GITHUB_TOKEN`을 설정한 다음
서버를 시작합니다. 토큰은 채팅·프로젝트 JSON·프런트엔드 코드에 넣지 않습니다.

Workshop의 GitHub 연결 설정에서 저장소 `owner/repo`, 기본 브랜치와 Pages URL을
입력하고 저장한 뒤 연결 확인을 누릅니다.

## 4. 게시

1. 프로젝트 설정에서 캡션과 해시태그를 편집합니다.
2. Instagram 게시 창에서 합쳐진 캡션을 확인합니다.
3. 지금 게시 또는 예약 게시를 선택합니다. 예약시간 입력은 한국 시간입니다.
4. 대기열로 전송하면 최신 카드 전체를 검사·렌더링하고 GitHub에 한 번에 올립니다.
5. 전송 완료 후 컴퓨터를 꺼도 됩니다. 상태 새로고침으로 결과를 확인하세요.

GitHub는 이미지를 Pages에 배포한 뒤 Instagram 컨테이너를 만들고 게시합니다.
예약 검사는 약 5분 간격이며 실행이 지연될 수 있습니다. 공개 저장소가 오랫동안
활동이 없으면 예약 실행이 비활성화될 수 있으므로 Actions 상태를 확인하세요.

검증된 원본은 1080×1350 sRGB PNG로 보관합니다. Instagram API 전송에는 별도
JPEG를 사용합니다. 전체 카드 수는 2~10장, 캡션+태그는 2,200자 이내입니다.

동일한 내용과 시간을 다시 보내면 동일한 작업으로 처리합니다. 내용이나 시간을
바꾸면 새 작업이므로 기존 예약과 중복되지 않는지 확인하세요. 이번 버전은 전송한
예약의 수정·취소 기능을 제공하지 않습니다.

`게시 결과 확인 필요`가 표시되면 Instagram 계정에서 먼저 확인하세요.
서버 응답이 끊겨 성공 여부가 불명확할 때 중복 게시를 방지하기 위해 자동으로
다시 게시하지 않습니다. `state` 파일을 지우면 중복 방지 기록이 사라집니다.

실제 게시 성공은 계정 연결 후 첫 게시로 검증해야 합니다. 로컬 테스트는
외부 API 응답을 대체한 동작 검증을 포함하며 실제 계정 권한을 대신 검증하지 않습니다.
