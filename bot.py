import praw
import asyncio
import aiohttp
import logging
import os
import uuid
import json

from config import Config
from stream import Twitch
from reddit import SubredditTask

class Bot:
    def __init__(self):
        self.load_config()
        self.reddit = praw.Reddit(client_id=self.config.client,
                                  client_secret=self.config.secret,
                                  user_agent=self.config.user_agent,
                                  username=self.config.username,
                                  password=self.config.password)

    def load_config(self):
        with open('config.json', 'r') as fp:
            self.config = Config(json.load(fp))

    def save_config(self):
        temp = f'{uuid.uuid4()}-config.json'
        with open(temp, 'w', encoding='utf-8') as tmp:
            json.dump(self.config.to_dict(), tmp, sort_keys=True, indent=4, separators=(',', ': '))

        os.replace(temp, 'config.json')

    async def start(self):
        # Since aiohttp is dumb I have to do some init stuff here
        self.loop = asyncio.get_event_loop()
        async with aiohttp.ClientSession(loop=self.loop) as session:
            self.session = session
            self.twitch = Twitch(session, self.config.twitch_client_id)

            subreddit_tasks = [
                SubredditTask(self, subreddit)
                for subreddit in self.config.subreddits
            ]

            await asyncio.gather(*[
                task.update()
                for task in subreddit_tasks
            ])

if __name__ == '__main__':
    fmt = '[{asctime}] [{levelname:<7}] {name}: {message}'
    logging.basicConfig(level=logging.INFO, style='{', datefmt='%Y-%m-%d %H:%M:%S', format=fmt)
    bot = Bot()
    try:
        asyncio.run(bot.start())
    except KeyboardInterrupt:
        pass
