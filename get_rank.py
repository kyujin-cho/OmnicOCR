import json
import time
import sys 
import settings 
import requests
import dateutil 
import datetime

import errors
import database
import test

servers = ['pc-oc', 'pc-eu', 'pc-as', 'pc-krjp', 'pc-na', 'pc-sa', 'pc-sea']
base_url = 'https://api.playbattlegrounds.com/shards'
header = {
  "Authorization": settings.api_key,
  "Accept": "application/vnd.api+json"
}

sleep_time = 6

db = database.OmnicDB()

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

def match_list(streamer, server, mock=False):
    url = base_url + '/' + server + '/matches?filter[playerNames]=' + streamer
    response = test.mock_functions.mock_get_match_list(streamer, server) if mock else requests.get(url, headers=header)
    if response.status_code != 200:
        return response.json()
    elif response.status_code == 401:
        raise errors.UnauthorizedError()
    elif response.status_code == 404:
        raise errors.DataNotFoundError()
    elif response.status_code == 429:
        raise errors.TooManyRequestsError()
    else:
        raise errors.PUBGUnknownError()

def telemetry(data, mock=False):
    latest_game = data['id']
    game_type, asset_id = data['attributes']['gameMode'], data['assets'][0]['id']
    
    telemetry_url = array_find(data['included'], [('type', 'asset'), ('id', asset_id)])['attributes']['URL']
    telemetry = test.mock_functions.mock_get_telemetry(telemetry_url) if mock else requests.get(telemetry_url, headers=header)
    return telemetry.json()

def get_ranking(telemetry):
    log_match_end_players = array_find(telemetry, [('_T', 'LogMatchEnd')])['characters']
    streamer_stat = array_find(log_match_end_players, [('name', streamer)])
    return streamer_stat['ranking']

def get_kills(telemetry):
    kills = 0
    for d in telemetry:
        if d['_T'] == 'LogPlayerKill' and d['killer']['name'] == streamer:
            kills += 1
    return kills

def find_data_and_insert(data):
    telemetry_data = telemetry(data)
    rank, kills = get_ranking(telemetry_data), get_kills(telemetry_data)
    db.add_score(rank, kills, streamer, gametype=game_type)
    latest_game = data
    time.sleep(sleep_time * 2)

def check_rating(streamer):
    latest_game = None
    while True:
        for server in servers:
            response = None
            try:
                response = match_list(streamer, server)
            except Error as e:
                print(e)
                continue
            data = response['data'][0]
            if latest_game == None and dateutil.parser.parse(data['attributes']['createdAt']) > datetime.datetime.now().time() \
            or latest_game != None and dateutil.parser.parse(data['attributes']['createdAt']) > dateutil.parser.parse(latest_game['attributes']['createdAt']):
                find_data_and_insert(data)                

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