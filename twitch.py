import requests
import json
from stream import Stream

def update_streams(streams, result, game):
    # update the stream list
    for stream in streams:
        # the stream has 1 or more viewers
        channel = stream['channel']
        if stream['viewers'] and channel:
            try:
                name = channel['name']
                url = channel.get('url') or 'http://twitch.tv/' + name
                status = channel.get('status') or '' # handle None case
                result.append(Stream(url=url, viewers=stream['viewers'], display_name=channel['display_name'], game=game, status=status))
            except Exception as e:
                name = channel.get('name', 'null')
                print('Something happened over at channel {} for game {}'.format(name, game))
                print('{}: {}'.format(type(e).__name__, str(e)))
                with open(name + '_error_dump.json', 'w') as f:
                    json.dump(stream, f, indent=4)
                    print('A JSON dump has been provided at ' + f.name)

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
