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
top_cut | integer | How many streams to display in the sidebar at most
delay | integer | Length between updates in seconds.
wiki | string | The wiki page name to update.
games | array of strings | A list of games to search Twitch on
format | dictionary | A key value pair of games to format for the sidebar

An example `config.json` is given below.

```js
{
    "delay": 1800,
    "password": "mypassword",
    "subreddit": "mycoolsubreddit",
    "top_cut": 10,
    "user_agent": "Livestream updater for /r/testing -- written by /u/rapptz",
    "username": "mycoolusername",
    "wiki": "livestreams",
    "games": [
        "Super Smash Bros. Melee",
        "Super Smash Bros. for Nintendo 3DS",
        "Super Smash Bros. for Wii U",
        "Project M",
        "Super Smash Bros."
    ],

    "format": {
        "Super Smash Bros. Melee": "[^^**Melee** **{name}**{viewers}]({url})",
        "Super Smash Bros. for Nintendo 3DS": "[^^^^^**Smash3DS** **{name}**{viewers}]({url})",
        "Super Smash Bros. for Wii U": "[^^^^^^**SmashWiiU** **{name}**{viewers}]({url})",
        "Project M": "[^^^^**ProjectM** **{name}**{viewers}]({url})",
        "Super Smash Bros.": "[^^^**Smash64** **{name}**{viewers}]({url})"
    }
}

```

Currently only twitch is supported.

The bot also writes to this configuration file with minimum and maximum records which should not be touched.

## Running and Dependencies

There are a couple dependencies.

- [praw](https://github.com/praw-dev/praw), which is used for the reddit API integration.
- [requests](https://github.com/kennethreitz/requests/) which is used for the HTTP requests.

Installing the dependencies should be as easy as doing:

    pip install praw && pip install requests

On the command line.

Once you have those dependencies set up and the configuration above is valid, you can run the bot yourself by doing `python bot.py`. There's
a tutorial to help you set it up for your own subreddit in [the wiki][tut].

If the configuration is invalid, then the bot will tell you so.

[tut]: https://github.com/HypestTeam/livestreambot/wiki/Using-On-Your-Own-Subreddit

## License

The code is MIT licensed. You can check the license in the LICENSE file.
