import subprocess
import requests
import sys
import json
import threading

token_url = 'https://api.twitch.tv/api/vods/{}/access_token?adblock=false&need_https=false&oauth_token&platform=web&player_type=site'
m3u8_url = 'https://usher.ttvnw.net/vod/218144553.m3u8?allow_source=true&nauthsig={}&player_backend=mediaplayer&rtqos=realtime&baking_bread=false&fast_bread=false&nauth={}'

command = [
    'ffmpeg',
    '-ss', '0',
    '-i', 'FILLME',
    '-y',
    '-ss', 'FILLME',
    '-frames:v', '1', 'FILLME'
]

threads = []

def chunkIt(seq, num):
    avg = len(seq) / float(num)
    out = []
    last = 0.0

    while last < len(seq):
        out.append(seq[int(last):int(last + avg)])
        last += avg

    return out

def dl_files(l, url):
    for ts in l:
        p = subprocess.Popen('curl {}/{} > {}'.format('/'.join(url.split('/')[:-1]), ts, ts))
        p.wait()

for id in sys.argv[1:]:
    token = requests.get(token_url.format(id), headers={
        'client-id': 'jzkbprff40iqj646a697cyrvl0zt2m6'
    })
    nauthsig = token.json()['sig']
    token = json.dumps(token.json()['token'])
    m3u8 = requests.get(m3u8_url.format(nauthsig, json.dumps(token).replace('\\', '')[1:-1])).text
    chunked = list(filter(lambda x: 'chunked/index-dvr.m3u8' in x, m3u8.split('\n')))[0]
    ts_files = chunkIt(list(filter(lambda x: '.ts' in x, chunked)), 4)
    for ts_file in ts_files:
        threads.append(threading.Thread(target=dl_files, args=(ts_file,chunked,)))
        threads[-1].start()
    for thread in threads:
        thread.wait()
    
        