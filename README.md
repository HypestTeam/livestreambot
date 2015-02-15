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

An example `config.json` is given below.

```js
{
    "username": "myboy",
    "password": "mypassword",
    "subreddit": "testing",
    "user_agent": "Livestream Bot for /r/testing -- written by /u/rapptz",
    "top_cut": 10,
    "delay": 900,
    "wiki": "livestreams"
}
```

Currently only twitch is supported.

## Running and Dependencies

The bot is just a self-contained python script, to run it just execute `python bot.py` and make
sure the configuration above is all set up. There are a couple dependencies.

- [praw](https://github.com/praw-dev/praw), which is used for the reddit API integration.
- [requests](https://github.com/kennethreitz/requests/) which is used for the HTTP requests.

## License

The code is MIT licensed. You can check the license in the LICENSE file.
