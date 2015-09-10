import requests
import json
from stream import Stream

game_to_id = {}

def prepare_game_id_cache(games):
    for game in games:
        if game in game_to_id:
            continue

        payload = {
            'q': game,
            'liveonly': True
        }

        r = requests.get('https://www.hitbox.tv/api/games', params=payload)
        if r.status_code == 200:
            data = r.json()
            for category in data.get('categories', {}):
                if category.get('category_name', '').lower() == game.lower():
                    game_to_id[game] = category['category_id']
                    break

def get_streams(games):
    prepare_game_id_cache(games)
    streams = []
    for game in games:
        game_id = game_to_id.get(game)
        if game_id is None:
            continue

        params = {
            'game': game_id,
            'liveonly': True,
            'showHidden': False,
            'publicOnly': True
        }
        r = requests.get('https://www.hitbox.tv/api/media/live/list', params=params)
        print('The hitbox API returned {} for {}'.format(r.status_code, game))
        if r.status_code == 200:
            data = r.json()
            for stream in data.get('livestream', []):
                kwargs = {
                    'url': stream.get('channel', {}).get('channel_link', ''),
                    'viewers': int(stream.get('media_views', 0)),
                    'display_name': stream.get('media_user_name', ''),
                    'game': game,
                    'status': stream.get('media_status', '')
                }

                streams.append(Stream(**kwargs))

    return streams
