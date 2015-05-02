#!/usr/bin/env python
from __future__ import print_function
import twitch
import re, json, sys
import praw
from datetime import datetime
import time
import xml.sax.saxutils as saxutils

config = {}

def get_updated_sidebar_portion(streams):
    result = ['###### START STREAM LIST\n']
    game_to_format = config['format']
    for stream in streams[0:config.get('top_cut', 10)]:
        temp = '- '
        temp += game_to_format.get(stream.game, '[{name}]({url}) {viewers} viewers')
        result.append(temp.format(name=stream.display_name, url=stream.url, viewers=stream.viewers))
        result.append('')

    result.append('\n###### END STREAM LIST')
    return '\n'.join(result)

def get_config():
    with open('config.json') as f:
        return json.load(f)

def verify_valid_config():
    required_entries = ['user_agent', 'username', 'password', 'subreddit', 'games', 'format']
    failure = False
    error_message = ['bot configuration is valid']
    for entry in required_entries:
        if entry not in config:
            failure = True
            error_message.append('    note: could not find value for key "{}"'.format(entry))

    stream = sys.stdout
    if failure:
        error_message[0] = 'fatal error: could not configure bot properly'
        stream = sys.stderr

    print('\n'.join(error_message), file=stream)
    if failure:
        sys.exit(1)

def update_config():
    with open('config.json', 'w') as f:
        twitch.prettify_json(config, f)

def prepare_bot():
    r = praw.Reddit(config['user_agent'])
    r.login(config['username'], config['password'])
    return r

def update_sidebar(reddit, streams):
    print('updating sidebar...')
    # get the old sidebar
    settings = reddit.get_settings(config['subreddit'])
    old_sidebar = saxutils.unescape(settings['description']) # work around for html escape garbage
    new_portion = get_updated_sidebar_portion(streams)
    new_sidebar = re.sub(r'###### START STREAM LIST.*?###### END STREAM LIST', new_portion, old_sidebar, count=1, flags=re.DOTALL)
    reddit.update_settings(reddit.get_subreddit(config['subreddit']), description=new_sidebar)
    print('done...')

def get_record(rec, total, today, fmt, func):
    entry = config.get(rec, None)
    entry_record = config.get(rec + '_record', None)

    if entry and func(total, entry) or entry == None and entry_record == None:
        entry = total
        entry_record = today.strftime(fmt)
        config[rec] = total
        config[rec + '_record'] = entry_record
        update_config()

    return (entry, entry_record)

def update_wiki(reddit, streams):
    print('updating wiki...')
    subreddit = config['subreddit']
    interval = config['delay']
    strftime_str = '%b %d %Y at %I:%M %p'
    result = ['Welcome to the /r/{} livestream page!\n'.format(subreddit)]
    result.append('This page is automatically updated by /u/{name} and should not be edited. This page currently '
                  'gets updated every {t} minutes. If something seems wrong, please contact the subreddit '
                  'moderators.\n'.format(name=config['username'], t=interval/60))

    today = datetime.now()
    total = 0
    result.append('### Streams')
    result.append('')
    result.append(today.strftime('This page was last updated on {}\n'.format(strftime_str)))
    result.append('Game Name | Stream | Viewers | Status ')
    result.append(':---------|:-------|:-------:|:-------')
    for stream in streams:
        total += stream.viewers
        status = stream.status.replace('|', '&#124;') # escape special character for tables
        result.append('{0.game}|[{0.display_name}]({0.url})|{0.viewers}|{1}'.format(stream, status))

    # check for minimum and maximum
    (minimum, minimum_record) = get_record('minimum', total, today, strftime_str, lambda x,y: x < y)
    (maximum, maximum_record) = get_record('maximum', total, today, strftime_str, lambda x,y: x > y)

    result.append('')
    result.append('### Statistics')
    result.append('')
    result.append('Total number of viewers: {}\n'.format(total))
    result.append('Lowest number of total viewers: {} on {}\n'.format(minimum, minimum_record))
    result.append('Highest number of total viewers: {} on {}'.format(maximum, maximum_record))
    result.append('')
    reddit.edit_wiki_page(reddit.get_subreddit(subreddit), config.get('wiki', 'livestreams'), '\n'.join(result), 'Bot action')
    print('done...')

def attempt_update(reddit, streams):
    try:
        update_sidebar(reddit, streams)
        update_wiki(reddit, streams)
    except Exception as e:
        # try again in 1 minute
        print('An error has occurred: {}, trying again in one minute...'.format(str(e)))
        time.sleep(60)
        attempt_update(reddit, streams)

if __name__ == '__main__':
    config = get_config()
    verify_valid_config()
    reddit = prepare_bot()
    while True:
        print(datetime.now().strftime('Current time %X'))
        streams = twitch.get_streams(config['games'])
        attempt_update(reddit, streams)
        time.sleep(config.get('delay', 1800))
