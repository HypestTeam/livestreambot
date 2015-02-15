#!/usr/bin/env python
import twitch
import re, json, sys
import praw
from datetime import datetime
import time
import xml.sax.saxutils as saxutils

game_to_format = {
    'Super Smash Bros. Melee': '[^^**Melee** **{name}**{viewer}]({url})',
    'Super Smash Bros. for Nintendo 3DS': '[^^^^^**Smash3DS** **{name}**{viewer}]({url})',
    'Super Smash Bros. for Wii U': '[^^^^^^**SmashWiiU** **{name}**{viewer}]({url})',
    'Project M': '[^^^^**ProjectM** **{name}**{viewer}]({url})',
    'Super Smash Bros.': '[^^^**Smash64** **{name}**{viewer}]({url})'
}

config = {}

def get_updated_sidebar_portion(streams):
    result = ['###### START STREAM LIST\n']
    for stream in streams[0:config.get('top_cut', 10)]:
        temp = '- '
        temp += game_to_format[stream.game]
        result.append(temp.format(name=stream.display_name, url=stream.url, viewer=stream.viewers))
        result.append('')

    result.append('\n###### END STREAM LIST')
    return '\n'.join(result)

def get_config():
    with open('config.json') as f:
        return json.load(f)

def prepare_bot():
    try:
        r = praw.Reddit(config['user_agent'])
        r.login(config['username'], config['password'])
        return r
    except Exception as e:
        print('fatal error occured: could not configure bot')
        print('note: possibly forgot to write config.json')
        print('note: "username", "user_agent", "subreddit", and "password" fields are required')
        print('The exception string was as follows:')
        print(e)
        sys.exit(1)

def update_sidebar(reddit, streams):
    print('updating sidebar...')
    # get the old sidebar
    settings = reddit.get_settings(config['subreddit'])
    old_sidebar = saxutils.unescape(settings['description']) # work around for html escape garbage
    new_portion = get_updated_sidebar_portion(streams)
    new_sidebar = re.sub(r'###### START STREAM LIST.*?###### END STREAM LIST', new_portion, old_sidebar, count=1, flags=re.DOTALL)
    reddit.update_settings(reddit.get_subreddit(config['subreddit']), description=new_sidebar)
    print('done...')

def update_wiki(reddit, streams):
    print('updating wiki...')
    subreddit = config['subreddit']
    interval = config['delay']
    result = ['Welcome to the /r/{} livestream page!\n'.format(subreddit)]
    result.append('This page is automatically updated by /u/{name} and should not be edited. This page currently '
                  'gets updated every {t} minutes. If something seems wrong, please contact the subreddit '
                  'moderators.\n'.format(name=config['username'], t=interval/60))

    today = datetime.now()
    total = 0
    result.append(today.strftime('This page was last updated on %c\n'))
    result.append('Game Name | Stream | Viewers')
    result.append(':---------|:-------|:-------:')
    for stream in streams:
        total += stream.viewers
        result.append('{0.game}|[{0.display_name}]({0.url})|{0.viewers}'.format(stream))

    result.append('')
    result.append('Total number of viewers: {}'.format(total))
    reddit.edit_wiki_page(reddit.get_subreddit(subreddit), config.get('wiki', 'livestreams'), '\n'.join(result), 'Bot action')
    print('done...')

if __name__ == '__main__':
    config = get_config()
    reddit = prepare_bot()
    while True:
        print(datetime.now().strftime('Current time %X'))
        streams = twitch.get_streams()
        update_sidebar(reddit, streams)
        update_wiki(reddit, streams)
        time.sleep(config.get('delay', 900))
