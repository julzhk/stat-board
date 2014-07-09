import tornado.ioloop
import tornado.web
import requests
import config
import atexit

from apscheduler.scheduler import Scheduler
from time import time
from datetime import datetime
from pymongo import Connection
from tornado.options import define, options, parse_command_line

define("port", default=8080, help="run on the given port", type=int)

clients = []

sched = Scheduler()

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("templates/index.html")



def instagram_counts(filter=None):
    con = Connection()
    db = con.statboard
    sm = db.socialmedia
    # for stat in sm.find():
    #     sm.remove(stat)
    for instauser in config.instagram_users:
        r = requests.get(
            'https://api.instagram.com/v1/users/%s/?client_id=%s'
            % (instauser['id'], config.instagram_client_id)
        )
        r = r.json()

        insert = {
            'service': 'instagram',
            'user_account': instauser['user'],
            'datetime': int(time()),
            'followers': r['data']['counts']['followed_by']
        }

        sm.insert(insert)
    for stat in sm.find():
        print stat

    return True

class Collector(tornado.web.RequestHandler):
    def get(self, filter):

        instagram_counts()

        self.render("templates/index.html")


class EventSchedule(tornado.web.RequestHandler):
    def get(self):
        sched.print_jobs()


sched = Scheduler(daemon=True)
atexit.register(lambda: sched.shutdown())
sched.add_cron_job(instagram_counts, minute="*/15")
# sched.add_cron_job(instagram_counts, minute="*/5", args=['blah'])

sched.start()

app = tornado.web.Application([
    (r'/', IndexHandler),
    (r'/collect/(.*)', Collector),
    (r'/schedule', EventSchedule),
])

if __name__ == '__main__':
    parse_command_line()
    app.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()