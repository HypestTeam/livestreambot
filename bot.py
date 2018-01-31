#!/usr/bin/env python
from __future__ import print_function
import twitch, hitbox
import re, json, sys
import praw
from datetime import datetime
import time
import xml.sax.saxutils as saxutils
import requests
import requests.auth
import traceback

config = {}
subreddit_config = {}
MAX_SIDEBAR_LENGTH = 10240

def prettify_json(js, f):
    json.dump(js, f, sort_keys=True, indent=4, separators=(',', ': '))

def get_updated_sidebar_portion(streams, count):
    result = ['###### START STREAM LIST\n']
    game_to_format = subreddit_config['format']
    for stream in streams[0:count]:
        temp = '- '
        game_format = game_to_format.get(stream.game, None)
        if not game_format:
            game_format = '[{name}]({url}) {viewers} viewers'
        temp += game_format
        result.append(temp.format(name=stream.display_name.strip(), url=stream.url, viewers=stream.viewers))

    result.append('\n###### END STREAM LIST')
    return '\n'.join(result)

def get_config():
    with open('config.json') as f:
        return json.load(f)

def verify_valid_config():
    required_entries = ['user_agent', 'username', 'password', 'client',
                        'secret', 'redirect', 'delay', 'subreddits', 'twitch_client_id']
    failure = False
    error_message = ['bot configuration seems valid']
    for entry in required_entries:
        if entry not in config:
            error_message.append('note: could not find value for key "{}"'.format(entry))

    # verify 'subreddits' key is valid
    sub_keys = ['name', 'format', 'wiki']
    subreddits = config.get('subreddits', None)
    if subreddits:
        for subreddit in subreddits:
            for key in sub_keys:
                if key not in subreddit:
                    error_message.append(('note: missing required key ("{}") in "subreddits" object'.format(key)))

    stream = sys.stdout
    failure = len(error_message) > 1
    if failure:
        error_message[0] = 'fatal error: could not configure bot properly'
        stream = sys.stderr

    print('\n'.join(error_message), file=stream)
    if failure:
        sys.exit(1)

def update_config():
    with open('config.json', 'w') as f:
        prettify_json(config, f)

def get_oauth_token():
    auth = requests.auth.HTTPBasicAuth(config['client'], config['secret'])
    data = { 'grant_type': 'password', 'username': config['username'], 'password': config['password'] }
    headers = { 'User-Agent': config['user_agent'] }
    response = requests.post('https://www.reddit.com/api/v1/access_token', auth=auth, data=data, headers=headers)
    result = response.json()
    if result['scope'] == '*':
        result['scope'] = set('creddits edit flair history identity modconfig modcontributors '
                              'modflair modlog modothers modposts modself modwiki mysubreddits '
                              'privatemessages read report save submit subscribe vote wikiedit wikiread'.split(' '))

    return result

def prepare_bot():
    r = praw.Reddit(config['user_agent'])
    # set the app info
    r.set_oauth_app_info(config['client'], config['secret'], config['redirect'])
    token = get_oauth_token()
    r.set_access_credentials(token['scope'], token['access_token'])
    return r

def update_sidebar(reddit, streams):
    print('updating sidebar...')
    # get the old sidebar
    subreddit = subreddit_config['name']
    settings = reddit.get_settings(subreddit)
    old_sidebar = saxutils.unescape(settings['description']) # work around for html escape garbage
    count = subreddit_config.get('top_cut', 10)
    while count != 0:
        new_portion = get_updated_sidebar_portion(streams, count)
        new_sidebar = re.sub(r'###### START STREAM LIST.*?###### END STREAM LIST', new_portion, old_sidebar, count=1, flags=re.DOTALL)

        if len(new_sidebar) <= MAX_SIDEBAR_LENGTH:
            reddit.update_settings(reddit.get_subreddit(subreddit), description=new_sidebar)
            break

        count = int(count / 2)
        print('Sidebar too long... trying again with {} streams'.format(count))

    print('done...')

def get_record(rec, total, today, fmt, func):
    entry = subreddit_config.get(rec, None)
    entry_record = subreddit_config.get(rec + '_record', None)

    if (entry is None and entry_record is None) or (entry is not None and func(total, entry)):
        entry = total
        entry_record = today.strftime(fmt)
        subreddit_config[rec] = total
        subreddit_config[rec + '_record'] = entry_record
        update_config()

    return (entry, entry_record)

def sanitize_input(data):
    """Sanitizes input for reddit markdown tables"""
    data = data.replace('|', '&#124;')
    data = data.replace('\n', '')
    data = data.replace('*', '\\*')
    return data

def update_wiki(reddit, streams):
    print('updating wiki...')
    subreddit = subreddit_config['name']
    interval = config['delay']
    strftime_str = '%b %d %Y at %I:%M %p UTC'
    result = ['Welcome to the /r/{} livestream page!\n'.format(subreddit)]
    result.append('This page is automatically updated by /u/{name} and should not be edited. This page currently '
                  'gets updated every {t} minutes. If something seems wrong, please contact the subreddit '
                  'moderators or /u/rapptz.\n'.format(name=config['username'], t=interval/60))

    today = datetime.utcnow()
    total = 0
    result.append('### Streams')
    result.append('')
    result.append(today.strftime('This page was last updated on {}\n'.format(strftime_str)))
    result.append('Game Name | Stream | Viewers | Status ')
    result.append(':---------|:-------|:-------:|:-------')
    for stream in streams:
        total += stream.viewers
        status = sanitize_input(stream.status)
        result.append('{0.game}|[{0.display_name}]({0.url})|{0.viewers}|{1}'.format(stream, status))

    # check for minimum and maximum
    (maximum, maximum_record) = get_record('maximum', total, today, strftime_str, lambda x,y: x > y)

    result.append('')
    result.append('### Statistics')
    result.append('')
    result.append('Total number of viewers: {}\n'.format(total))
    result.append('Highest number of total viewers: {} on {}'.format(maximum, maximum_record))
    result.append('')
    reddit.edit_wiki_page(reddit.get_subreddit(subreddit), subreddit_config.get('wiki', 'livestreams'), '\n'.join(result), 'Bot action')
    print('done...')

def get_games():
    return subreddit_config['format'].keys()

def attempt_update(reddit, streams):
    try:
        update_sidebar(reddit, streams)
        update_wiki(reddit, streams)
    except praw.errors.OAuthException as e:
        raise e
    except praw.errors.APIException as e:
        print('An error has occurred:')
        traceback.print_exc()
        print('Skipping...')
    except Exception as e:
        # try again in 1 minute
        print('An error has occurred while updating streams.')
        traceback.print_exc()
        print('Trying again in 1 minute.')
        time.sleep(60)
        attempt_update(reddit, streams)

def attempt_streams(games):
    try:
        streams = twitch.get_streams(games)
        if subreddit_config.get('hitbox', False):
            streams.extend(hitbox.get_streams(games))

        # sort based on viewers
        streams.sort(key=lambda x: x.viewers, reverse=True)
        return streams
    except praw.errors.OAuthException as e:
        raise e
    except Exception as e:
        # error happened here so attempt to retry
        print('An error has occurred:')
        traceback.print_exc()
        print('Trying again in 5 minutes...')
        time.sleep(60 * 5)
        return attempt_streams(games)

def run():
    try:
        global config
        global subreddit_config
        config = get_config()
        verify_valid_config()
        reddit = prepare_bot()
        subreddits = config['subreddits']
        if reddit.is_oauth_session():
            print('OAuth2 Login Successful')
        else:
            raise RuntimeError('OAuth2 session is unsuccessful')
    except Exception as e:
        print('An internal error has occurred')
        traceback.print_exc()
        raise e
    else:
        twitch.set_client_id(config['twitch_client_id'])
        while True:
            try:
                for subreddit in subreddits:
                    print('Updating /r/{}'.format(subreddit['name']))
                    print(datetime.now().strftime('Current time %X'))
                    subreddit_config = subreddit
                    streams = attempt_streams(get_games())
                    attempt_update(reddit, streams)

                time.sleep(config.get('delay', 1800))
            except praw.errors.OAuthException as e:
                # we got an OAuth error (I think)
                token = get_oauth_token()
                reddit.set_access_credentials(token['scope'], token['access_token'])

def main():
    while True:
        try:
            run()
        except Exception:
            print('Waiting 5 minutes to retry...')
            time.sleep(60 * 5.0)

if __name__ == '__main__':
    main()
