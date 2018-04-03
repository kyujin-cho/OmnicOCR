import pytest
import requests
import get_rank
import errors
import json
import os

array_find_data = [
     {
        'foo': 'bar',
        'some': '1',
        'other': '$',
        'bool': True,
        'number': 123
    },
    {
        'foo': 'asd',
        'some': '1',
        'other': '$',
        'bool': True,
        'number': 12
    },
    {
        'foo': 'bar',
        'some': '3',
        'other': '#',
        'bool': True,
        'number': 12
    },
    {
        'foo': 'efd',
        'some': '4',
        'other': '$',
        'bool': False,
        'number': 456
    }
]

player_data = None
match_data = None
telemetry_data = None

with open('test/data/players/pc-oc_Funzinnu', 'r') as fr:
    player_data = json.loads(fr.read())

with open('test/data/matches/438031fe-6ff9-4b6a-b0ea-37eb4eac5ae5', 'r') as fr:
    match_data = json.loads(fr.read())

with open('test/data/telemetry/e59b54b1-35c6-11e8-acca-0a5864631f81', 'r') as fr:
    telemetry_data = json.loads(fr.read())

def pytest_sessionstart(session):
    print('Clearing id cache file before test...')
    clear_id()

def clear_id():
    with open('id_cache', 'w') as fw:
        fw.write('')

def test_should_contain_all_auth_informations():
    for key in ['db_host', 'db_user', 'db_password', 'db', 'ClientID', 'pubg_api_key']:
        assert 'omnic_' + key in os.environ.keys()

def test_should_auth_properly():
    res = requests.get(get_rank.base_url + '/pc-krjp/players', headers=get_rank.header)
    assert res.status_code == 404

def test_should_raise_contaminated_id():
    with open('id_cache', 'w') as fw:
        fw.write('foo=bar=1234\n')
    with pytest.raises(errors.CacheIDContaminatedError):
        print(get_rank.get_cached_ids())

def test_should_raise_contaminated_id_regex():
    with open('id_cache', 'w') as fw:
        fw.write('foo=b$r\n')
    with pytest.raises(errors.CacheIDContaminatedError):
        get_rank.get_cached_ids()
    

def test_should_get_multiple_ids():
    with open('id_cache', 'w') as fw:
        fw.write('foo=account.bar\n')
        fw.write('asd=account.1234\n')
        fw.write('143d=account.elj149fk\n')
    pids = get_rank.get_cached_ids()
    expected_ids = {
        'foo': 'account.bar',
        'asd': 'account.1234',
        '143d': 'account.elj149fk'
    }
    assert expected_ids == pids

def test_should_get_no_ids():
    clear_id()
    pids = get_rank.get_cached_ids()
    assert pids == {}

def test_should_put_one_id():
    clear_id()
    get_rank.cache_pid('foo', 'bar')
    text = ''
    with open('id_cache', 'r') as fr:
        text = fr.read()
    assert text == 'foo=bar\n'

def test_should_put_multiple_ids():
    clear_id()
    get_rank.cache_pid('foo', 'bar')
    get_rank.cache_pid('adsd', '123')
    get_rank.cache_pid('1', '4r4f')
    get_rank.cache_pid('11kfj', '9dk')
    text = ''
    with open('id_cache', 'r') as fr:
        text = fr.read()
    assert text == 'foo=bar\nadsd=123\n1=4r4f\n11kfj=9dk\n'

def test_should_find_item_in_array():
    found = get_rank.array_find(array_find_data, [('other', '#')])
    assert found == array_find_data[2]

def test_should_only_one_find_item_in_array_multi_cond():
    found = get_rank.array_find(array_find_data, [('bool', True), ('some', '3')])
    assert found == array_find_data[2]

def test_should_return_appropriate_boolean():
    latest_game = {
        'attributes': {
            'updatedAt': ''
        }
    }
    assert not get_rank.latest_cond(None, '2018-04-01T16:21:34Z')
    
    latest_game['attributes']['updatedAt'] = '2018-04-01T16:34:34Z'
    assert not get_rank.latest_cond(latest_game, '2018-04-01T16:21:34Z')
    
    assert get_rank.latest_cond(None, '2020-04-01T16:12:34Z')

    latest_game['attributes']['updatedAt'] = '2018-03-01T16:21:34Z'
    assert get_rank.latest_cond(latest_game, '2018-04-01T16:21:34Z')

def test_should_get_player():
    player = get_rank.get_player('Funzinnu', 'pc-oc')
    assert player['id'] == 'account.693077e0f54246849359a78d7ce50505'
    with open('id_cache', 'w') as fw:
        fw.write('Funzinnu=account.693077e0f54246849359a78d7ce50505\n')
    get_rank.playerIDs = get_rank.get_cached_ids()
    player = get_rank.get_player('Funzinnu', 'pc-oc')
    assert player['id'] == 'account.693077e0f54246849359a78d7ce50505'

def test_should_raise_not_found():
    with pytest.raises(errors.DataNotFoundError):
        get_rank.get_player('0xFFMark', 'pc-sea')

def test_should_find_telemetry_url_from_data():
    assert get_rank.get_telemetry_url(match_data) == 'https://telemetry-cdn.playbattlegrounds.com/bluehole-pubg/pc-krjp/2018/04/01/16/08/e59b54b1-35c6-11e8-acca-0a5864631f81-telemetry.json'
    
def test_should_get_rank_kills_game_type():
    rank, kills, game_type = get_rank.get_ranking(telemetry_data, '0xFFMark'), get_rank.get_kills(telemetry_data, '0xFFMark'), get_rank.get_game_type(match_data)
    assert game_type == 'squad'
    assert kills == 0 
    assert rank == 1
    

