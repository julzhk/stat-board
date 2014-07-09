import tornado.ioloop
import tornado.web
import requests
import config

from time import time
from pymongo import Connection
from tornado.options import define, options, parse_command_line

define("port", default=8080, help="run on the given port", type=int)

clients = []

class IndexHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        self.render("templates/index.html")


class Collector(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self, filter):

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

        self.render("templates/index.html")



app = tornado.web.Application([
    (r'/', IndexHandler),
    (r'/collect/(.*)', Collector),
])

if __name__ == '__main__':
    parse_command_line()
    app.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()