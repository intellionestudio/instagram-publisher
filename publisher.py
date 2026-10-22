"""GitHub Actions runner. Checkpoints are persisted BEFORE Instagram publishes."""
import base64
import hashlib
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode, quote, urlparse
from urllib.request import Request, urlopen


def request(method, url, token='', data=None, form=False):
    encoded = (urlencode(data).encode() if form else json.dumps(data).encode()) if data is not None else None
    headers = {'User-Agent': 'Carousel-Workshop', 'Accept': 'application/json'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    if encoded is not None:
        headers['Content-Type'] = 'application/x-www-form-urlencoded' if form else 'application/json'
    try:
        with urlopen(Request(url, data=encoded, headers=headers, method=method), timeout=60) as response:
            raw = response.read()
            return json.loads(raw) if raw else {}
    except HTTPError as exc:
        # Provider bodies may contain access tokens. Log status only.
        raise RuntimeError(f'API HTTP {exc.code}; check account permissions/token and provider dashboard') from None


class Store:
    def __init__(self):
        self.base = 'https://api.github.com/repos/' + os.environ['GITHUB_REPOSITORY'] + '/contents/state/'
        self.token = os.environ['GH_TOKEN']
        self.branch = os.environ['PUBLISH_BRANCH']

    def save(self, state):
        state['updated_at'] = datetime.now(timezone.utc).isoformat()
        url = self.base + state['job_id'] + '.json'
        payload = {'message': 'Record publish state ' + state['status'], 'branch': self.branch,
                   'content': base64.b64encode(json.dumps(state, ensure_ascii=False, indent=2).encode()).decode()}
        if state.get('_sha'):
            payload['sha'] = state['_sha']
        # Do not store internal GitHub revision identifiers in the payload.
        clean = {key: value for key, value in state.items() if key != '_sha'}
        payload['content'] = base64.b64encode(json.dumps(clean, ensure_ascii=False, indent=2).encode()).decode()
        result = request('PUT', url, self.token, payload)
        state['_sha'] = result['content']['sha']

    def load(self, job_id):
        # Checkout is refreshed for every serialized run. Read API too for checkpoint SHAs.
        local = Path('state') / (job_id + '.json')
        if not local.exists():
            return {'job_id': job_id, 'status': 'queued'}
        result = request('GET', self.base + job_id + '.json?ref=' + quote(self.branch, safe=''), self.token)
        return {**json.loads(base64.b64decode(result['content'])), '_sha': result['sha']}


class Instagram:
    def __init__(self):
        host = os.environ.get('INSTAGRAM_GRAPH_HOST', 'graph.instagram.com')
        version = os.environ.get('INSTAGRAM_API_VERSION', '')
        account = os.environ.get('INSTAGRAM_ACCOUNT_ID', '')
        if host not in {'graph.instagram.com', 'graph.facebook.com'} or not re.fullmatch(r'v\d+\.\d+', version) or not account.isdigit():
            raise ValueError('Configure INSTAGRAM_API_VERSION, INSTAGRAM_GRAPH_HOST and INSTAGRAM_ACCOUNT_ID')
        self.base = 'https://' + host + '/' + version + '/'
        self.account = account
        self.token = os.environ['INSTAGRAM_ACCESS_TOKEN']

    def create(self, data):
        return request('POST', self.base + self.account + '/media', self.token, data, True)['id']

    def status(self, container):
        return request('GET', self.base + container + '?fields=status_code', self.token)['status_code']

    def wait(self, container):
        for _ in range(36):
            status = self.status(container)
            if status == 'FINISHED':
                return
            if status in {'ERROR', 'EXPIRED'}:
                raise RuntimeError('Instagram container ' + status)
            time.sleep(5)
        raise RuntimeError('Instagram processing timed out')

    def publish(self, container):
        return request('POST', self.base + self.account + '/media_publish', self.token,
                       {'creation_id': container}, True)['id']


def due(job, now):
    if job['mode'] == 'immediate':
        return True
    if job['mode'] != 'scheduled':
        raise ValueError('Invalid publish mode')
    date = datetime.fromisoformat(job['scheduled_at'])
    if date.tzinfo is None:
        raise ValueError('Missing schedule timezone')
    return date <= now


def validate_job(job, directory):
    if not re.fullmatch(r'post-[a-f0-9]{32}', job['job_id']) or directory.name != job['job_id']:
        raise ValueError('Invalid job identity')
    if not 2 <= len(job['media']) <= 10 or not 1 <= len(job['caption']) <= 2200:
        raise ValueError('Invalid carousel count or caption length')
    for item in job['media']:
        if not re.fullmatch(r'\d{2}\.jpg', item['file']):
            raise ValueError('Invalid image path')
        if hashlib.sha256((directory / item['file']).read_bytes()).hexdigest() != item['sha256']:
            raise ValueError('Image digest mismatch')


def run_job(job, state, store, instagram, directory, pages_url):
    if state['status'] == 'publishing':
        # An interrupted media_publish may have succeeded. Never publish a second time.
        if state.get('container_id') and instagram.status(state['container_id']) == 'PUBLISHED':
            state['status'] = 'published'
        else:
            state['status'] = 'needs_review'
            state['error'] = '이전 게시 요청의 결과를 확정할 수 없습니다. Instagram 계정에서 확인해 주세요.'
        store.save(state)
        return
    if state['status'] != 'queued':
        return
    try:
        validate_job(job, directory)
        if job['pages_url'] != pages_url:
            raise ValueError('Pages URL differs from PAGES_BASE_URL')
        state['status'] = 'preparing'
        store.save(state)
        children = []
        for item in job['media']:
            url = pages_url + '/media/' + job['job_id'] + '/' + item['file']
            # Ensure the deployed file is available, exact and anonymous before Meta fetches it.
            for attempt in range(12):
                try:
                    with urlopen(url, timeout=60) as response:
                        data = response.read()
                    if hashlib.sha256(data).hexdigest() != item['sha256']:
                        raise ValueError('Public image digest mismatch')
                    break
                except Exception:
                    if attempt == 11:
                        raise ValueError('Public image is unavailable or does not match the queued image') from None
                    time.sleep(5)
            child = instagram.create({'image_url': url, 'is_carousel_item': 'true',
                                      'alt_text': item.get('alt_text', '')})
            instagram.wait(child)
            children.append(child)
        container = instagram.create({'media_type': 'CAROUSEL', 'children': ','.join(children),
                                      'caption': job['caption']})
        instagram.wait(container)
        state['container_id'] = container
        state['status'] = 'publishing'
        store.save(state)  # If this fails, media_publish MUST NOT be called.
        try:
            state['media_id'] = instagram.publish(container)
            state['status'] = 'published'
        except Exception:
            state['status'] = 'needs_review'
            state['error'] = '게시 요청 결과를 확정할 수 없습니다. 재게시 전에 Instagram에서 확인해 주세요.'
        store.save(state)
    except Exception as exc:
        if state['status'] in {'publishing', 'published', 'needs_review'}:
            # Retain the durable publishing checkpoint for reconciliation on the next run.
            raise
        state['status'] = 'failed'
        state['error'] = str(exc) if isinstance(exc, ValueError) else '게시 준비 실패. Actions 로그와 계정 설정을 확인해 주세요.'
        store.save(state)


def main():
    pages_url = os.environ.get('PAGES_BASE_URL', '').rstrip('/')
    parsed = urlparse(pages_url)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.query or parsed.fragment:
        raise ValueError('Set PAGES_BASE_URL to your public HTTPS Pages URL')
    store, instagram = Store(), Instagram()
    for directory in sorted(Path('queue').glob('post-*')):
        path = directory / 'post.json'
        if not path.is_file():
            continue
        job = json.loads(path.read_text())
        if not due(job, datetime.now(timezone.utc)):
            continue
        state = store.load(job['job_id'])
        if state['status'] == 'preparing':
            state['status'] = 'failed'
            state['error'] = '이전 준비 작업이 중단되었습니다. 자동 재게시하지 않았습니다.'
            store.save(state)
            continue
        run_job(job, state, store, instagram, directory, pages_url)
        print(job['job_id'] + ': ' + state['status'])


if __name__ == '__main__':
    main()
