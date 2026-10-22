# Personal Instagram publisher

Use a dedicated repository containing only this template and queued media. Do not
upload the Carousel Workshop repository, private project originals or credentials.

1. Create a repository with these files, including `.github/workflows/publish.yml`
   and `state/.gitkeep`, on its default branch (normally `main`).
2. Settings → Pages → Source: GitHub Actions. Public repositories support Pages on
   GitHub Free. Images deployed to Pages are public. Private-source Pages requires
   an eligible plan and does not make the published images private.
3. Settings → Secrets and variables → Actions → Secrets:
   `INSTAGRAM_ACCOUNT_ID`, `INSTAGRAM_ACCESS_TOKEN` (Instagram professional account
   with content publishing permission). Obtain credentials from Meta's developer
   dashboard, never put them in files. Instagram Login uses
   `instagram_business_basic`, `instagram_business_content_publish`.
4. Actions Variables:
   `PAGES_BASE_URL` = exact Pages site URL without trailing slash;
   `INSTAGRAM_API_VERSION` = the supported Graph API version shown in your Meta app
   (e.g. `v25.0`, verify before use);
   `INSTAGRAM_GRAPH_HOST` = `graph.instagram.com` for Instagram Login, or
   `graph.facebook.com` for Facebook Login with the corresponding token.
5. Run the workflow manually once to verify configuration. Scheduling may be
   delayed, and GitHub can disable schedules in inactive public repositories.
6. On the local machine, set `WORKSHOP_GITHUB_TOKEN` before starting the Workshop
   server. Use a fine-grained token for this repository with Contents read/write.
   It does not need workflow-write permission: install this template yourself.
7. In Workshop, enter repository, default branch and Pages URL; check connection.
   Open Instagram publishing, review the caption, choose now or schedule, and send.

The local app renders current content to validated 1080×1350 sRGB PNG, retains
the originals, and generates JPEG derivatives because Instagram's image publishing
API accepts JPEG. Maximum 10 cards; combined caption + tags maximum 2,200 characters.
Metadata stays in `queue/post-*/post.json`; only JPEG files are copied to Pages.

State is stored durably in `state/<job-id>.json`. `queued → preparing → publishing
→ published`. Failures are `failed` or `needs_review`. Never delete state files
or manually requeue `publishing`/`needs_review` without checking Instagram first.
The same content and schedule has a stable ID; repeated transmission does not
create a second post. Changing the content or schedule creates a new job, so check
existing reservations before doing that. Scheduling is processed by GitHub about
every five minutes, not an exact-time guarantee. Token expiration requires renewal
in Secrets; automatic token renewal is not provided by this template.

Official references:
- https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/content-publishing/
- https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages
- https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule
