import json
import requests.exceptions

class NotFoundError(Exception):
    def __str__(self):
        return "Requested URL not found in mock server!"
def get(url):
    if 'api.playbattlegrounds.com' in url:
        return get_player(url)
    else:
            requests.exceptions.RequestException()

def get_player(url):
    surl = url.replace('https://api.playbattlegrounds.com/').split('/')
    class ResData:
        def __init__(self, jdata):
            self.data = jdata
        def json(self):
            return self.data
    if len(surl) == 3:
        server = surl[1]
        playerName = surl[2].split('=')[1]
        try:
            with open('data/players/{}_{}'.format(server, playerName), 'r') as fr:
                res = ResData(json.loads(fr.read()))
                return res
        except FileNotFoundError as e:
            requests.exceptions.RequestException()
    elif len(surl) == 4:
        server = surl[1]
        pid = surl[3]
        try:
            with open('data/players_by_id/{}_{}'.format(server, pid), 'r') as fr:
                res = ResData(json.loads(fr.read()))
                return res
        except FileNotFoundError as e:
            requests.exceptions.RequestException()
        else:
            requests.exceptions.RequestException()