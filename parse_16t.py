import urllib.request
import urllib.parse
import urllib.error
import threading
import sys
import time
import subprocess
import pyocr
import pyocr.builders
import requests
import settings
import pymysql
import os
import os.path
import sys

from PIL import Image
class OmnicDB:
    def __init__(self):
        self.conn = pymysql.connect(host=settings.host, user=settings.user, password=settings.password, db=settings.db, charset='utf8', autocommit=True)
        self.curs = self.conn.cursor()

    def add_score(self, rank, streamer_id, gametype='솔로'):
        self.conn.ping(True)
        sql = 'select `series` from `broadcast` where `streamer_id`=%s order by `series` desc limit 1;'
        self.curs.execute(sql, streamer_id)
        rows = self.curs.fetchall()
        series = rows[0][0]

        sql = 'insert into `score`(`series`, `rank`, `type`, `streamer_id`) value(%s, %s, %s, %s)'
        self.curs.execute(sql, (series, rank, gametype, streamer_id))

a = OmnicDB()
check = -1
lock = threading.RLock()
tool = pyocr.get_available_tools()[0]
rank = '*'
ranks = []
init = True
isDuo = len(sys.argv) == 3 and sys.argv[2] == '1'

def ocr(ts, cnt, t, key): 
    global rank
    global a
    global check
    global tool
    global rank
    global ranks
    global init
    global isDuo
    command = [
        'ffmpeg',
        '-ss', '0',
        '-i', 'ts_s/' + ts + '.ts',
        '-y',
        '-ss', 'FILLME',
        '-frames:v', '1', 'FILLME'
    ]

    for j in range(1, 4):
        command[-4] = str((t/3) * (j-1))
        print(' '.join(command))
        command[-1] = 'ts_s/' + str(cnt) + '_' + ts + '_' + str(j) + '.jpg'
        p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # p = subprocess.Popen(command)
        p.wait()
        start, txt, txt_2 = '', '', ''
        start = tool.image_to_string(Image.open(command[-1]).crop((70, 655, 160, 695)), lang='pubg_start', builder=pyocr.builders.TextBuilder())
        if 'START' in start or 'RSART' in start or 'RSTAT' in start:
            isDuo = ('RSART' in start or 'RSTAT' in start)
            init = True
            print('Started MATCHMAKING... Setting init to True...')
        if init:
            Image.open(command[-1]).crop((160, 170, 220, 210) if isDuo else (120, 170, 180, 210)).save(command[-1].replace('.jpg', '_crop.jpg'))
            Image.open(command[-1]).crop((1060, 20, 1155, 85)).convert('LA').save(command[-1].replace('.jpg', '_crop_gs.png'))
            p = subprocess.Popen('tesseract {} stdout -l pubg -psm 7'.format(command[-1].replace('.jpg', '_crop.jpg')).split(' '), stdout=subprocess.PIPE, stderr=None)
            p.wait()
            txt = p.communicate()[0].decode('utf-8').split('\n')[0]
            p2 = subprocess.Popen('tesseract {} stdout -l pubg -psm 7'.format(command[-1].replace('.jpg', '_crop_gs.png')).split(' '), stdout=subprocess.PIPE, stderr=None)
            p2.wait()
            txt_2 = p2.communicate()[0].decode('utf-8').split('\n')[0]
            with lock:
                if 4 > len(txt) > 1 and txt[0] == '#' and txt[1:].isnumeric() and int(txt[1:]) > 0 and txt == txt_2 and not ('RSART' in start) and not ('START' in start):
                    if rank == '*':
                        rank = txt
                        check = 1
                    else:
                        if rank == txt:
                            check += 1
                            if check == 3:
                                ranks.append(txt)
                                a.add_score(int(txt[1:]), key, gametype=('팀' if isDuo else '솔로'))
                                updated = True
                                init = False
                        else:
                            check = 1
                            rank = txt
                    print(txt, check)
        print(command[-1])
        print(t)
        print(txt, '/', txt_2, '/', start) 

def check_rating(key):
    p = subprocess.Popen('sudo rm -rf ts_s'.split(' '))
    p.wait()
    os.mkdir('ts_s')
    print('PUBG turned on')
    get_token = 'https://api.twitch.tv/api/channels/{}/access_token?'.format(key)
    get_token += urllib.parse.urlencode({
        'adblock':'false', 
        'need_https':'false',
        'oauth_token':'',
        'platform':'web',
        'player_type':'site'
    })
    get_token = requests.get(get_token, headers={'Client-ID': settings.ClientID}).json()
    print(get_token)
    token = get_token['token']
    sig = get_token['sig']

    base = 'https://usher.ttvnw.net/api/channel/hls/{}.m3u8?'.format(key)
    base += urllib.parse.urlencode({
        'allow_source': 'true', 
        'baking_bread': 'false', 
        'fast_bread': 'false', 
        'player_backend': 'mediaplayer', 
        'rtqos': 'control', 
        'sig': sig,
        'token': token
    })
    base = urllib.request.urlopen(base).read().decode('utf-8').split('\n')
    ind = 0
    for i in base:
        print(i)
        if '720p' in i:
            break
        ind += 1
    url = base[ind+2]

    
    ranks = []
    cnt=1
    init = True
    try:
        print(url)
        while True:
            updated = False
            load = urllib.request.urlopen(url).read().decode('utf-8').split('\n')[6:-1]
            index = 0
            while not load[index].startswith('#EXTINF'):
                index += 1
            
            print('Loads')
            print('\n'.join(load))
            print('Index:', index)
            time_diff = 0
            print('Waiting for {} rank...'.format('Duo' if isDuo else 'Solo') if init else '')
            threads = []

            for i in range(index, len(load), 2):
                start_ = time.time()
                print('123'+ load[i])
                t = float(load[i][8:-5])
                ts_url = load[i+1]
                if not load[i+1].startswith('http'):
                    ts_url = ('/').join(url.split('/')[:-1]) + '/' +load[i+1]
                    print(ts_url)
                with open('ts_s/' + str(i//2+1) + '.ts', 'wb') as fw:
                    fw.write(urllib.request.urlopen(ts_url).read())
                threads.append(threading.Thread(target=ocr, args=(str(i//2+1),cnt,t,key,)))
                threads[-1].start()
                threads[-1].wait()

                print(time.time() - start_)       
                time_diff += (t - (time.time() - start_))
                
            print(ranks)
            cnt += 1
            if updated:
                print('rank updated! Setting init to False...')
            elif time_diff > 0:
                print('Sleeping', time_diff)
                time.sleep(time_diff)
    except: 
        return

on = False
print('Waiting for stream...')
while not on:
    try:
        response = requests.get('https://api.twitch.tv/helix/streams?user_login=' + sys.argv[1], headers={'Client-ID': settings.ClientID})
        headers = response.headers
        response = response.json()
        print('Limit:',headers['RateLimit-Limit'])
        print('Remaining:', headers['RateLimit-Remaining'])
        on = (response != None and response['data'] != None and len(response['data']) != 0 and (response['data'][0]['game_id'] == '493057'))
    except KeyError as e: 
        print('Error!', e)
        print('Error!', response)
    except ConnectionResetError as e1:
        print('Error!', e1)
        print('Error!', response)
    except ConnectionError as e2:
        print('Error!', e2)
        print('Error!', response)
    time.sleep(3)
print('Stream started. Starting omnic...')
check_rating(sys.argv[1])
print('Stream ended. Performing scheduled restart...')
