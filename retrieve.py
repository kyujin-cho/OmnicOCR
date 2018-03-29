import json
import time
import sys 
import settings 
import requests
import dateutil 
import datetime
import pymysql


servers = ['pc-oc', 'pc-eu', 'pc-as', 'pc-krjp', 'pc-na', 'pc-sa', 'pc-sea']
base_url = 'https://api.playbattlegrounds.com/shards'
endpoint = 'matches'
header = {
  "Authorization": settings.api_key,
  "Accept": "application/vnd.api+json"
}

sleep_time = 6

class OmnicDB:
    def __init__(self):
        self.conn = pymysql.connect(host=settings.host, user=settings.user, password=settings.password, db=settings.db, charset='utf8', autocommit=True)
        self.curs = self.conn.cursor()

    def add_score(self, rank, kills, streamer_id, gametype='솔로'):
        self.conn.ping(True)
        sql = 'select `series` from `broadcast` where `streamer_id`=%s order by `series` desc limit 1;'
        self.curs.execute(sql, streamer_id)
        rows = self.curs.fetchall()
        series = rows[0][0]

        sql = 'insert into `score`(`series`, `rank`, `kills`, type`, `streamer_id`) value(%s, %s, %s, %s, %s)'
        self.curs.execute(sql, (series, rank, gametype, streamer_id))
        self.cool = time.time()
        try:
            requests.get('http://127.0.0.1:13947')
        except:
            print('',end='')

db = OmnicDB()

def array_find(l, conditions):
    for i in l:
        match = True
        for condition in conditions:
            if i[condition[0]] != i[condition[1]]:
                match = False
                break
        if match:
            return i
    return None

def check_rating(streamer):
    latest_game = None
    while True:
        for server in servers:
            url = base_url + '/' + server + '/' + endpoint
            url += '?filter[playerNames]=' + streamer
            response = requests.get(url, headers=header)
            if response.status_code != 200:
                continue
            
            data = response.json()['data'][0]
            if latest_game == None and dateutil.parser.parse(data['attributes']['createdAt']) > datetime.datetime.now().time():
                latest_game = data['id']
                game_type, asset_id = data['attributes']['gameMode'], data['assets'][0]['id']
                
                telemetry_url = array_find(data['included'], [('type', 'asset'), ('id', asset_id)])['attributes']['URL']
                telemetry = requests.get(telemetry_url, headers=header)
                telemetry_data = telemetry.json()
                
                log_match_end_players = array_find(telemetry_data, [('_T', 'LogMatchEnd')])['characters']
                streamer_stat = array_find(log_match_end_players, [('name', streamer)])
                rank = streamer_stat['ranking']

                kills = 0
                for d in telemetry_data:
                    if d['_T'] == 'LogPlayerKill' and d['killer']['name'] == streamer:
                        kills += 1
                
                db.add_score(rank, kills, streamer, gametype=game_type)
                


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
