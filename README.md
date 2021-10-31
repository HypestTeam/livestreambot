## Live Stream Bot

Live Stream Bot is a bot that fetches the streams for Smash Bros. games to display in the
sidebar and in the wiki of [/r/smashbros](http://reddit.com/r/smashbros). It is currently live
under [/u/superstreambot](http://reddit.com/u/superstreambot).

The bot is essentially configurable (to a certain extent), you can check near the bottom on how to configure it.

## Configuration

The bot expects a `config.json` file to be in the current directory with the current values:

Key | Value Type | Description
:----|:-----------|:-----------
username | string | The reddit username
password | string | The reddit password
user_agent | string | The bot's user agent
delay | integer | Length between updates in seconds.
subreddits | list of objects | A list of objects that gives information of what subreddits to update
client | string | The app client ID (for OAuth2)
secret | string | The app's client secret (for OAuth2)
twitch_client_id | string | The Client ID used for Twitch API requests.

Likewise, the subreddits object requires these keys:

Key | Value Type | Description
:----|:----------|:------------
name | string | The subreddit name
widget | object | The sidebar widget settings to update (new reddit)
top_cut | integer | How many streams to display in the sidebar at most
wiki | string | The wiki page name to update.
format | dictionary | A key value pair of games to format for the sidebar

The widget object requires these keys:

Key | Value Type | Description
:----|:----------|:------------
name | string | The widget name to update (case sensitive)
table | boolean | Whether to use a simple table to update the text with

If the widget doesn't use the simple table then it falls back to the format list.

An example `config.json` is given below.

```js
{
    "username": "myusername",
    "password": "mypassword",
    "delay": 1800,
    "user_agent": "Livestream updater -- written by /u/rapptz",
    "subreddits": [
        {
            "format": {
                "Project M": "[^^^^**ProjectM** **{name}**{viewers}]({url})",
                "Super Smash Bros.": "[^**Smash64** **{name}**{viewers}]({url})",
                "Super Smash Bros. Brawl": "[^^^**Brawl** **{name}**{viewers}]({url})",
                "Super Smash Bros. Melee": "[^^**Melee** **{name}**{viewers}]({url})",
                "Super Smash Bros. for Nintendo 3DS": "[^^^^^**Smash3DS** **{name}**{viewers}]({url})",
                "Super Smash Bros. for Wii U": "[^^^^^^**SmashWiiU** **{name}**{viewers}]({url})"
            },
            "name": "smashbros",
            "top_cut": 10,
            "wiki": "livestreams",
            "widget": {
                "name": "Live Streams",
                "table": true
            }
        }
    ]
}


```

Currently only twitch is supported.

The bot also writes to this configuration file with minimum and maximum records which should not be touched.

## Running and Dependencies

### Easy Way

If you want your subreddit to use the bot without running your own instance, just send a private message to /u/rapptz and
he'll tell you what to do from there.

### Manual Way

There are a couple dependencies.

- [praw](https://github.com/praw-dev/praw), which is used for the reddit API integration.
- [aiohttp](https://github.com/aio-libs/aiohttp) which is used for the HTTP requests.

Note that this bot requires Python 3.7 or higher.

Installing the dependencies should be as easy as doing:

    pip install praw && pip install aiohttp

On the command line.

Once you have those dependencies set up and the configuration above is valid, you can run the bot yourself by doing `python bot.py`. There's
a tutorial to help you set it up for your own subreddit in [the wiki][tut].

If the configuration is invalid, then the bot will tell you so.

[tut]: https://github.com/HypestTeam/livestreambot/wiki/Using-On-Your-Own-Subreddit

## License

The code is MIT licensed. You can check the license in the LICENSE file.
