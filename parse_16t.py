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
import imagehash
import os
import os.path
import sys
import traceback

RED   = "\033[1;31m"  
BLUE  = "\033[1;34m"
CYAN  = "\033[1;36m"
GREEN = "\033[0;32m"
RESET = "\033[0;0m"
BOLD    = "\033[;1m"
REVERSE = "\033[;7m"

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
        self.cool = time.time()

a = OmnicDB()

duo_hash = imagehash.average_hash(Image.open('duo_crop.png'))
lock = threading.RLock()

lockvals = {
    'ranks' : [],
    'check' : 0,
    'rank' : '*'
}
nonlockvals = {
    'cnt' : 1,
    'init' : True,
    'isTeam' : len(sys.argv) == 3 and sys.argv[2] == '1',
    'teamType' : 0 # 0 if duo, 1 if squad
}
tool = pyocr.get_available_tools()[0]

def ocr(i, t, key):
    global duo_hash
    global a
    global lock
    global lockvals
    global nonlockvals
    global tool
    start_ = time.time()
    command = [
        'ffmpeg',
        '-ss', '0',
        '-i', 'ts_s/' + str(i//2+1) + '.ts',
        '-y',
        '-ss', 'FILLME',
        '-frames:v', '1', 'FILLME'
    ]
    updated = False
    data = {
        'start': [],
        'txt': [],
        'txt_2': []
    }
    for j in range(1, 4):
        command[-4] = str((t/3) * (j-1))
        # print('T' + str(i//2+1), ':', ' '.join(command))
        command[-1] = 'ts_s/' + str(nonlockvals['cnt']) + '_' + str(i//2+1) + '_' + str(j) + '.jpg'
        p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # p = subprocess.Popen(command)
        p.wait()
        start, txt, txt_2 = '', '', ''
        start = tool.image_to_string(Image.open(command[-1]).crop((70, 655, 160, 695)), lang='pubg_start', builder=pyocr.builders.TextBuilder())
        if 'START' in start or 'RSART' in start or 'RSTAT' in start:
            nonlockvals['isTeam'] = ('RSART' in start or 'RSTAT' in start)
            nonlockvals['init'] = True
            hashval = -1
            if nonlockvals['isTeam']:
                current_hash = imagehash.average_hash(Image.open(command[-1]).crop((40, 470, 190, 495)))
                hash_2 = imagehash.average_hash(Image.open(command[-1]).crop((40, 540, 190, 565)))
                hashval = abs(current_hash - duo_hash)
                hashval2 = abs(hash_2 - duo_hash)
                if hashval > 15:
                    hashval = hashval2 
                if hashval <= 4:
                    nonlockvals['teamType'] = 0
                else:
                    nonlockvals['teamType'] = 1
                    
            print('T' + str(i//2+1), ':', 'Started MATCHMAKING... Setting init to True...', '/ Hash Diff value:', hashval, '/', nonlockvals['teamType'])
        if nonlockvals['init']:
            Image.open(command[-1]).crop((160, 170, 220, 210) if nonlockvals['isTeam'] else (120, 170, 180, 210)).save(command[-1].replace('.jpg', '_crop.jpg'))
            Image.open(command[-1]).crop((1060, 20, 1155, 85)).convert('LA').save(command[-1].replace('.jpg', '_crop_gs.png'))
            p = subprocess.Popen('tesseract {} stdout -l pubg -psm 7'.format(command[-1].replace('.jpg', '_crop.jpg')).split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            p.wait()
            txt = p.communicate()[0].decode('utf-8').split('\n')[0]
            p2 = subprocess.Popen('tesseract {} stdout -l pubg -psm 7'.format(command[-1].replace('.jpg', '_crop_gs.png')).split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            p2.wait()
            txt_2 = p2.communicate()[0].decode('utf-8').split('\n')[0]
            data['start'].append(start)
            data['txt'].append(txt)
            data['txt_2'].append(txt_2)
            
            with lock:
                if 4 > len(txt) > 1 and txt[0] == '#' and txt[1:].isnumeric() and int(txt[1:]) > 0 and txt == txt_2 and not ('RSART' in start) and not ('START' in start):
                    if lockvals['rank'] == '*':
                        lockvals['rank'] = txt
                        lockvals['check'] = 1
                    else:
                        if lockvals['rank'] == txt:
                            lockvals['check'] += 1
                            if lockvals['check'] == 3:
                                lockvals['ranks'].append(txt)
                                a.add_score(int(txt[1:]), key, gametype=(('듀오' if nonlockvals['teamType'] == 0 else '스쿼드') if nonlockvals['isTeam'] else '솔로'))
                                updated = True
                                nonlockvals['init'] = False
                        else:
                            lockvals['check'] = 1
                            lockvals['rank'] = txt
                    # print('T' + str(i//2+1), ':', txt, lockvals['check'])
        # print('T' + str(i//2+1), ':', command[-1])
        # print('T' + str(i//2+1), ':', t)
        # print('T' + str(i//2+1), ':', txt, '/', txt_2, '/', start, '/', end=' ')
        # if nonlockvals['isTeam']:
        #     print('T' + str(i//2+1), ':', 'Duo' if nonlockvals['teamType'] == 0 else 'Squad')
        # else:
        #     print('T' + str(i//2+1), ':', 'Solo')
        # if updated:
        #     print('T' + str(i//2+1), ':', 'rank updated! Setting init to False...')
    print('T' + str(i//2+1), ':', data)  


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

    
    try:
        print(url)
        while True:
            start_ = time.time()
            print('Started at', start_)
            threads = []
            updated = False
            load = urllib.request.urlopen(url).read().decode('utf-8').split('\n')[6:-1]
            index = 0
            while not load[index].startswith('#EXTINF'):
                index += 1
            
            print('Index:', index)
            total_time =0.0
            
            print('Waiting for {} rank...'.format((('듀오' if nonlockvals['teamType'] == 0 else '스쿼드') if nonlockvals['isTeam'] else '솔로') if nonlockvals['init'] else ''))
            for i in range(index, len(load), 2):
                t = float(load[i][8:-5])
                ts_url = load[i+1]
                if not load[i+1].startswith('http'):
                    ts_url = ('/').join(url.split('/')[:-1]) + '/' +load[i+1]
                    print(ts_url)
                with open('ts_s/' + str(i//2+1) + '.ts', 'wb') as fw:
                    fw.write(urllib.request.urlopen(ts_url).read())
                total_time += t

                threads.append(threading.Thread(target=ocr, args=(i,t,key,)))
                threads[-1].start()
            [t.join() for t in threads]    
            time_diff = time.time() - start_       
                
            print(lockvals['ranks'])
            nonlockvals['cnt'] += 1
            if total_time - time_diff > 0:
                print('Sleeping', total_time - time_diff)
                print('Ended at', time.time(), '. Should be restarted at',time.time() + total_time - time_diff)     
                time.sleep(total_time - time_diff)
    except Exception as e:
        sys.stdout.write(RED)
        traceback.print_exc()
        sys.stdout.write(RESET)
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
