from collections import OrderedDict
import config
import atexit
from apscheduler.schedulers.tornado import TornadoScheduler
import json
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from os import path, environ
from time import time
import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.httpserver
from tornado.websocket import WebSocketClosedError
from tornado.options import define, options, parse_command_line
from pymongo import Connection, MongoClient
import random

import social_media_fetcher
import analytic_fetcher

define("port", default=8080, help="run on the given port", type=int)

# List of all the clients connected via websockets
clients = []

def get_social_media_data():
    try:
        client = MongoClient(environ['MONGOLAB_URI'])
        db = client.get_default_database()
    except:
        con = Connection()
        db = con.statboard
    return db.socialmedia


class TemplateRendering(object):

    def render_template(self, template_name, variables):
        template_dirs = []
        template_dirs.append(path.join(path.dirname(__file__), 'templates')) # added a default for fail over.
        env = Environment(loader = FileSystemLoader(template_dirs))
        try:
            template = env.get_template(template_name)
        except TemplateNotFound:
            raise TemplateNotFound(template_name)
        content = template.render(variables)
        return content


class TestHandler(tornado.web.RequestHandler, TemplateRendering):
    def get(self):
        self.write('test')


class IndexHandler(tornado.web.RequestHandler, TemplateRendering):

    def get_data(self, username, service):
            sm = get_social_media_data()
            return sm.find({"user_account": username, "service": service}).sort("_id", -1).limit(40)

    def user_loop(self, users, service):
        r = []
        for user in users:
            r.append({
                'name': user['name'],
                'data': self.get_data(user['user'], service)
            })
        return r

    def get(self):
        data = dict()
        data['host'] = self.request.host

        data['insta_spark'] = self.user_loop(config.INSTAGRAM_USERS, 'instagram')
        data['twitter_spark'] = self.user_loop(config.TWITTER_USERS, 'twitter')
        data['pinterest_spark'] = self.user_loop(config.PINTEREST_USERS, 'pinterest')
        data['facebook_spark'] = self.user_loop(config.FACEBOOK_PAGE, 'facebook')
        data['youtube_spark'] = self.user_loop(config.YOUTUBE_USERS, 'youtube')
        data['linkedin_spark'] = self.user_loop(config.LINKEDIN_USERS, 'linkedin')

        content = self.render_template('index.html', data)
        self.write(content)


class AnalyticsHandler(tornado.web.RequestHandler, TemplateRendering):

    def get(self):
        from analytics.analytics  import get_top_pages
        data = {'pages':get_top_pages()}
        content = self.render_template('googledash.html', data)
        self.write(content)


class DashHandler(tornado.web.RequestHandler, TemplateRendering):
    def group_data(self, incoming):
        out = OrderedDict()
        for cur in incoming:
            fuzzy_date = str(cur['datetime'])[:-1]
            try:
                out[fuzzy_date]['details'].append(cur)
            except KeyError:
                out[fuzzy_date] = {'total': 0, 'details': []}
                out[fuzzy_date]['details'].append(cur)
            out[fuzzy_date]['total'] = out[fuzzy_date]['total'] + cur['followers']
        return out


    def get(self):

        data = {}
        sm = get_social_media_data()
        data['host'] = self.request.host
        data['facebook'] = self.group_data(sm.find({"service": 'facebook'}).sort("datetime", -1).limit(500))
        data['instagram'] = self.group_data(sm.find({"service": 'instagram'}).sort("datetime", -1).limit(500))
        data['twitter'] = self.group_data(sm.find({"service": 'twitter'}).sort("datetime", -1).limit(500))
        data['pinterest'] = self.group_data(sm.find({"service": 'pinterest'}).sort("datetime", -1).limit(500))
        data['analytics_overview'] = list(sm.find({"service": 'analytic_overview', "date": {"$gt": 1356998400}}).sort("date", -1).limit(730))
        data['analytic_zip'] = analytic_fetcher.analytic_zipper(data['analytics_overview'])

        content = self.render_template('dash.html', data)
        self.write(content)


class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def open(self, *args):
        clients.append(self)
        print "New web socket connection: %s" % self


def send_message(message=None):

    if not message:
        message = {"followers": random.randrange(17950, 17960), "user_account": "vamuseum", "service": "instagram", "datetime": int(time())}

    if type(message) is not dict:
        return

    if '_id' in message:
        del message['_id']
    send = json.dumps(message)

    for client in clients:
        try:
            client.write_message(send, False)
        except WebSocketClosedError:
            clients.remove(client)
            print 'Client exited'


def main():

    application = tornado.web.Application([
        (r'/', IndexHandler),
        (r'/dash', DashHandler),
        (r'/test', TestHandler),
        (r'/google', AnalyticsHandler),
        (r'/assets/(.*)', tornado.web.StaticFileHandler, {'path': './assets'},),
        (r'/ws/', WebSocketHandler)
    ])

    parse_command_line()
    application.listen(options.port)

    sched = TornadoScheduler(daemon=True)
    atexit.register(lambda: sched.shutdown())
    sched.add_job(social_media_fetcher.instagram_counts, 'cron', minute="*/1")
    sched.add_job(social_media_fetcher.twitter_counts, 'cron', minute="*/1")
    sched.add_job(social_media_fetcher.pinterest_counts, 'cron', minute="*/5")
    sched.add_job(social_media_fetcher.youtube_counts, 'cron', minute="*/5")
    sched.add_job(social_media_fetcher.facebook_counts, 'cron', minute="*/1")
    # todo reinstate when keys inserted 
    # sched.add_job(social_media_fetcher.linkedin_count, 'cron', minute="*/5")
    # Google Analytics importer
    sched.add_job(analytic_fetcher.get_results, 'cron', hour="1", minute="1")
    sched.start()

    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
