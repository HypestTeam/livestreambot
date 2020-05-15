import datetime
import asyncio
import logging
import yarl

from errors import RetryRequestLater

log = logging.getLogger(__name__)

class Stream:
    __slots__ = ('url', 'viewers', 'title', 'game', 'name')

    @classmethod
    def from_twitch(cls, data):
        self = cls.__new__(cls)
        self.name = data['user_name']
        self.url = f'https://twitch.tv/{self.name}'
        self.viewers = data['viewer_count']
        self.game = data['game_id']
        self.title =  data['title']
        return self

class Twitch:
    BASE_URL = yarl.URL('https://api.twitch.tv/helix/')
    def __init__(self, session, client_id, client_secret):
        self.session = session
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = None
        self.expires_in = datetime.datetime(1970, 1, 1)

    def get_ratelimit_delta(self, resp):
        reset = float(resp.headers['Ratelimit-Reset'])
        dt = datetime.datetime.fromutctimestamp(reset)
        delta = (dt - datetime.datetime.utcnow()).total_seconds()
        return delta

    async def fetch_token(self):
        params = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'client_credentials',
        }

        for i in range(3):
            async with self.session.post('https://id.twitch.tv/oauth2/token', params=params) as resp:
                log.info('Twitch Token Retrieval responded with %d', resp.status)
                if resp.status == 429:
                    delta = self.get_ratelimit_delta(resp)
                    log.warning('Ratelimited on %s for %.2f seconds', resp.url, delta)
                    await asyncio.sleep(delta)
                    continue

                if resp.status == 503:
                    log.warning('Service unavailable (%s). Retrying in 5 seconds...', resp.url)
                    await asyncio.sleep(5)
                    continue

                resp.raise_for_status()
                data = await resp.json()
                self.token = data['access_token']
                self.expires_in = datetime.datetime.utcnow() + datetime.timedelta(seconds=data['expires_in'])
                log.info('Received token that expires at %s', self.expires_in.isoformat())
                return

    async def request(self, method, path, *, params=None):
        now = datetime.datetime.utcnow()
        if now > self.expires_in:
            await self.fetch_token()

        headers = {
            'Authorization': f'Bearer {self.token}',
            'Client-ID': self.client_id,
        }

        for i in range(3):
            async with self.session.request(method, self.BASE_URL / path, params=params, headers=headers) as resp:
                log.info('Twitch API /%s responded with %d', path, resp.status)
                if resp.status == 429:
                    delta = self.get_ratelimit_delta(resp)
                    log.warning('Ratelimited on %s for %.2f seconds', resp.url, delta)
                    await asyncio.sleep(delta)
                    continue

                if resp.status == 503:
                    log.warning('Service unavailable (%s). Retrying in 5 seconds...', resp.url)
                    await asyncio.sleep(5)
                    continue

                if resp.status == 401:
                    data = await resp.json()
                    log.error('Unauthorized response: %s', data['message'])
                    resp.raise_for_status()

                resp.raise_for_status()
                return await resp.json()

    async def paginate(self, method, path, *, params=None, headers=None):
        paginating = True
        to_send = params
        while paginating:
            resp = await self.request(method, path, params=to_send, headers=headers)
            try:
                cursor = resp['pagination']['cursor']
            except KeyError:
                paginating = False
            else:
                if isinstance(params, list):
                    to_send = params + [('after', cursor)]
                elif isinstance(params, dict):
                    to_send = params.copy()
                    to_send['after'] = cursor
            yield resp['data']

    async def get_game_ids(self, game_names):
        params = [('name', name) for name in game_names]
        data = await self.request('GET', 'games', params=params)
        if data is None:
            raise RetryRequestLater('Could not get game IDs')

        return {
            x.get('id'): x.get('name')
            for x in data.get('data', [])
        }

    async def get_streams(self, game_ids):
        params = [('game_id', game_id) for game_id in game_ids]
        params.append(('first', 100))
        data = await self.request('GET', 'streams', params=params)
        if data is None:
            raise RetryRequestLater('Could not get streams by ID')
        return [Stream.from_twitch(d) for d in data.get('data', [])]
