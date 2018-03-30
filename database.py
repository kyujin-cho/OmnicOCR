import settings 
import pymysql

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
