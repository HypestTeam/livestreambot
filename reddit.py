import datetime
import aiohttp
import asyncio
import praw
import prawcore
import logging
import functools
import re

log = logging.getLogger(__name__)

def retry(seconds):
    def decorator(func):
        @functools.wraps(func)
        async def wrapped(self, *args, **kwargs):
            while True:
                try:
                    result = await func(self, *args, **kwargs)
                except (OSError,
                        aiohttp.ClientResponseError,
                        praw.exceptions.APIException,
                        asyncio.TimeoutError,
                        prawcore.exceptions.PrawcoreException) as e:
                    subreddit = self.subreddit.name
                    exc = f'{e.__class__.__module__}.{e.__class__.__qualname__}: {e}'
                    log.error('%s (for /r/%s) failed with %s. Retrying in %ds', func.__name__, subreddit, exc, seconds)
                    await asyncio.sleep(seconds)
                    continue
                else:
                    return result
        return wrapped
    return decorator

SIDEBAR_REGEX = re.compile(r'###### START STREAM LIST(.*?)###### END STREAM LIST', re.DOTALL)
MAX_SIDEBAR_LENGTH = 10240

def sanitize_input(data):
    """Sanitizes input for reddit markdown tables"""
    # TODO: maybe the rest of markdown?
    return data.replace('|', '&#124;').replace('\n', '').replace('*', '\\*')

class SubredditTask:
    """Represents an asynchronous task run at a specific time.

    This actually handles the work in a specific subreddit.
    """

    def __init__(self, bot, subreddit):
        self.bot = bot
        self.subreddit = subreddit
        self.time = datetime.datetime.utcnow()
        self._fetched_game_ids = False

    @retry(2 * 60.0)
    async def get_streams(self):
        formats = self.subreddit.format
        if not self._fetched_game_ids:
            mapping = await self.bot.twitch.get_game_ids(formats.keys())
            self.subreddit.game_ids = mapping
            self._fetched_game_ids = True
            self.bot.save_config()

        game_ids = self.subreddit.game_ids
        # Sometimes our game_ids can have keys that aren't in the format.
        # Just ignore those
        to_pass = [game_id for game_id, name in game_ids.items() if name in formats]
        streams = await self.bot.twitch.get_streams(to_pass)

        # Convert game_ids into game names
        for stream in streams:
            try:
                stream.game = game_ids[stream.game]
            except KeyError:
                log.warning('Could not find a game_id associated with %s.', stream.game)

        streams.sort(key=lambda s: s.viewers, reverse=True)
        game_names = ', '.join(repr(x) for x in formats)
        log.info('Fetched %d streams for /r/%s: %s', len(streams), self.subreddit.name, game_names)
        return streams

    @property
    def sub(self):
        return self.bot.reddit.subreddit(self.subreddit.name)

    def get_updated_sidebar_portion(self, streams):
        result = ['###### START STREAM LIST\n']
        for stream in streams:
            fmt = self.subreddit.format.get(stream.game)

            # None or empty string
            if not fmt:
                fmt = '[{name}]({url}) {viewers} viewers'

            fmt = f'- {fmt}'
            result.append(fmt.format(name=stream.name, url=stream.url, viewers=stream.viewers))

        result.append('\n###### END STREAM LIST')
        return '\n'.join(result)

    def _update_sidebar(self, streams):
        mod = self.sub.mod
        settings = mod.settings()
        old_sidebar = settings['description']
        count = self.subreddit.top_cut
        while count != 0:
            to_replace = self.get_updated_sidebar_portion(streams[0:count])
            new_sidebar = SIDEBAR_REGEX.sub(to_replace, old_sidebar, count=1)
            if len(new_sidebar) <= MAX_SIDEBAR_LENGTH:
                mod.update(description=new_sidebar)
                break
            count = count // 2
            log.info('Sidebar for %s too long. Trying again with %d streams.', self.subreddit.name, count)

        log.info('Sidebar update complete for /r/%s.', self.subreddit.name)

    @retry(60.0)
    async def update_sidebar(self, streams):
        await self.bot.loop.run_in_executor(None, self._update_sidebar, streams)

    def _update_wiki(self, streams):
        wiki = self.sub.wiki
        name = self.subreddit.name
        interval = self.bot.config.delay
        fmt = '%b %d %Y at %I:%M %p UTC'
        result = [
            f'Welcome to the /r/{name} livestream page!\n',
            f'This page is automatically updated by /u/{self.bot.config.username} and should not be edited.' \
            f'This page currently gets updated every {interval // 60} minutes. If something seems wrong, ' \
             'please contact the subreddit moderators or /u/rapptz',
        ]

        now = datetime.datetime.utcnow()
        total = 0
        result.append('### Streams')
        result.append('')
        result.append(f'This page was last updated on {now:{fmt}}\n')
        result.append('Game Name | Stream | Viewers | Status ')
        result.append(':---------|:-------|:-------:|:-------')
        for stream in streams:
            total += stream.viewers
            title = sanitize_input(stream.title)
            result.append(f'{stream.game}|[{stream.name}]({stream.url})|{stream.viewers}|{title}')

        # Check maximum record
        sub = self.subreddit
        if sub.maximum is None or total > sub.maximum:
            sub.maximum = total
            sub.maximum_record = format(now, fmt)
            self.bot.save_config()

        result.append('')
        result.append('### Statistics')
        result.append('')
        result.append(f'Total number of viewers: {total}\n')
        result.append(f'Highest number of total viewers: {sub.maximum} on {sub.maximum_record}')
        result.append('')

        wikipage = wiki[self.subreddit.wiki]
        wikipage.edit('\n'.join(result), reason='Bot action')
        log.info('Wiki update complete for /r/%s', name)

    @retry(60.0)
    async def update_wiki(self, streams):
        await self.bot.loop.run_in_executor(None, self._update_wiki, streams)

    async def update(self):
        delay = self.bot.config.delay
        name = self.subreddit.name
        while True:
            try:
                log.info('Beginning update on /r/%s', name)
                streams = await self.get_streams()
                await self.update_sidebar(streams)
                await self.update_wiki(streams)
                log.info('Completed update on /r/%s', name)
                await asyncio.sleep(delay)
            except KeyboardInterrupt:
                log.info('Received keyboard interrupt signal on SubredditTask for /r/%s', name)
                raise
