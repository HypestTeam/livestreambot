import requests
import json

class Stream(object):
    def __init__(self, **kwargs):
        self.url = kwargs.get('url', None)
        self.viewers = kwargs.get('viewers', None)
        self.display_name = kwargs.get('display_name', None)
        self.game = kwargs.get('game', None)
        self.status = kwargs.get('status', 'No status').encode('utf-8')

def prettify_json(js, f):
    json.dump(js, f, sort_keys=True, indent=4, separators=(',', ': '))

def update_streams(streams, result, game):
    # update the stream list
    for stream in streams:
        # the stream has 1 or more viewers
        channel = stream['channel']
        if stream['viewers'] and channel:
            try:
                result.append(Stream(url=channel['url'], viewers=stream['viewers'], display_name=channel['display_name'], game=game, status=channel['status']))
            except Exception as e:
                name = channel.get('name', 'null')
                print('Something happened over at channel {} for game {}'.format(name, game))

def get_game(stream_url, streams, game_name):
    r = requests.get(stream_url, params={'game': game_name })
    print('Status Code for "{}": {}'.format(game_name, r.status_code))
    if r.status_code != 200:
        return None

    js = r.json()
    iterate_streams = js['streams']
    update_streams(iterate_streams, streams, game_name)


def get_streams(games):
    base_url = 'https://api.twitch.tv/kraken/'
    stream_url = base_url + 'streams'
    streams = []

    # get the games
    for game in games:
        get_game(stream_url, streams, game)

    # sort based on viewers
    streams.sort(key=lambda x: x.viewers, reverse=True)
    return streams
