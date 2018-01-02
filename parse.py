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
from PIL import Image

log = open('log.txt', 'w')

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

class Status:
    def __init__(self):
        self.status = False
        self.item = ''


a = OmnicDB()

def log_text(*kwargs, prefix='I'):
    build = ' '.join([str(item) for item in kwargs])
    print(build)
    log.write(prefix + '-' + str(time.time()) + ':' + build + '\n')
    log.flush()

def check_rating(key, s):
    get_token = 'https://api.twitch.tv/api/channels/{}/access_token?'.format(key)
    get_token += urllib.parse.urlencode({
        'adblock':'false', 
        'need_https':'false',
        'oauth_token':'',
        'platform':'web',
        'player_type':'site'
    })
    get_token = requests.get(get_token, headers={'Client-ID': settings.ClientID}).json()
    log_text(get_token)
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
    print(list(filter(lambda s: '#EXT-X-MEDIA' in s, base)))
    ind = 0
    for i in base:
        print(i)
        if '720p' in i:
            break
        ind += 1
    url = base[ind+2]

    command = [
        'ffmpeg',
        '-ss', '0',
        '-i', 'FILLME',
        '-y',
        '-ss', 'FILLME',
        '-frames:v', '1', 'FILLME'
    ]
    tool = pyocr.get_available_tools()[0]
    ranks = []
    cnt=1
    check = 0
    rank = '*'
    init = True
    isDuo = len(sys.argv) == 2 and sys.argv[1] == '1'
    try:
        while s.status:
            updated = False
            load = urllib.request.urlopen(url).read().decode('utf-8').split('\n')[6:-1]

            time_diff = 0
            log_text('Waiting for {} rank...'.format('Duo' if isDuo else 'Solo') if init else '')
            for i in range(0, len(load), 2):
                start_ = time.time()
                t = float(load[i][8:-5])

                with open('ts_s/' + str(i//2+1) + '.ts', 'wb') as fw:
                    fw.write(urllib.request.urlopen(load[i+1]).read())

                command[4] = 'ts_s/' + str(i//2+1) + '.ts'
                for j in range(1, 4):
                    command[-4] = str((t/3) * (j-1))
                    print(' '.join(command))
                    command[-1] = 'ts_s/' + str(cnt) + '_' + str(i//2+1) + '_' + str(j) + '.jpg'
                    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    # p = subprocess.Popen(command)
                    p.wait()
                    start, txt = '', ''
                    start = tool.image_to_string(Image.open(command[-1]).crop((70, 655, 160, 695)), lang='pubg_start', builder=pyocr.builders.TextBuilder())
                    if 'START' in start or 'RSART' in start or 'RSTAT' in start:
                        isDuo = ('RSART' in start or 'RSTAT' in start)
                        init = True
                        log_text('Started MATCHMAKING... Setting init to True...')
                    if init:
                        Image.open(command[-1]).crop((160, 170, 220, 210) if isDuo else (120, 170, 180, 210)).save(command[-1].replace('.jpg', '_crop.jpg'))
                        p = subprocess.Popen('tesseract {} stdout -l pubg -psm 7'.format(command[-1].replace('.jpg', '_crop.jpg')).split(' '), stdout=subprocess.PIPE, stderr=None)
                        p.wait()
                        txt = p.communicate()[0].decode('utf-8').split('\n')[0]
                        if 4 > len(txt) > 1 and txt[0] == '#' and txt[1:].isnumeric():
                            if rank == '*':
                                rank = txt
                                check = 1
                            else:
                                if rank == txt:
                                    check += 1
                                    if check == 4:
                                        ranks.append(txt)
                                        a.add_score(int(txt[1:]), key, gametype=('듀오' if isDuo else '솔로'))
                                        updated = True
                                        init = False
                                else:
                                    check = 1
                                    rank = txt
                            log_text(txt, check)
                    log_text(command[-1])
                    log_text(t)
                    log_text(txt, '/', start) 
                log_text(time.time() - start_)       
                time_diff += (t - (time.time() - start_))
                
            log_text(ranks)
            cnt += 1
            if updated:
                log_text('rank updated! Setting init to False...')
            elif time_diff > 0:
                log_text('Sleeping', time_diff)
                time.sleep(time_diff)
    except urllib.error.HTTPError: 
        return

PUBGon = dict([(s, False) for s in settings.streamers])
threads = dict([(s, None) for s in settings.streamers])

s = Status()

while True:
    for streamer in PUBGon.keys():
        try:
            response = requests.get('https://api.twitch.tv/helix/streams?user_login=' + streamer, headers={'Client-ID': settings.ClientID})
            headers = response.headers
            response = response.json()
            log_text('Limit:',headers['RateLimit-Limit'])
            log_text('Remaining:', headers['RateLimit-Remaining'])
            PUBGon[streamer] = len(response['data']) != 0 and (response['data'][0]['game_id'] == '493057')
            if PUBGon[streamer] and threads[streamer] == None:
                threads[streamer] = threading.Thread(target=check_rating, args=(streamer,s,))
                s.status = True
                threads[streamer].start()
            elif not PUBGon[streamer] and threads[streamer] != None:
                s.status = False
                threads[streamer] = None
        except KeyError as e: 
            log_text(e, prefix='E')
            log_text(response, prefix='E')
        except ConnectionResetError as e1:
            log_text(e1, prefix='E')
            log_text(response, prefix='E')
        except ConnectionError as e2:
            log_text(e2, prefix='E')
            log_text(response, prefix='E')
        finally:
            time.sleep(3)