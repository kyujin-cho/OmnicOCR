import subprocess
import requests

token_url = 'https://api.twitch.tv/api/vods/{}/access_token?adblock=false&need_https=false&oauth_token&platform=web&player_type=site'
m3u8_url = 'https://usher.ttvnw.net/vod/218144553.m3u8?allow_source=true&nauthsig={}&player_backend=mediaplayer&rtqos=realtime&baking_bread=false&fast_bread=false&nauth={}'

for id in sys.argv[1:]:
    token = requests.get(token_url.format(id), headers={
        'client-id': 'jzkbprff40iqj646a697cyrvl0zt2m6'
    })
    nauthsig = token.json()['sig']
    m3u8 = requests.get(m3u8_url.format(nauthsig, token.text))
