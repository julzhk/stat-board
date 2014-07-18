import api_setup
import config
from collections import OrderedDict
import atexit
from apscheduler.scheduler import Scheduler
import json
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from os import path, environ
from time import gmtime, strftime, time
import tornado.ioloop
import tornado.web
from tornado import websocket
from tornado.websocket import WebSocketClosedError
from tornado.options import define, options, parse_command_line
from pymongo import Connection, MongoClient
from pymongo.errors import ConnectionFailure
import requests
from requests_oauthlib import OAuth1

import random

define("port", default=8080, help="run on the given port", type=int)
sched = Scheduler()

# List of all the clients connected via websockets
clients = []


def get_social_media_data():
    try:
        # on heroku
        client = MongoClient(environ['MONGOLAB_URI'])
        db = client.get_default_database()
    except (ConnectionFailure, KeyError, NameError):
        # locally
        con = Connection()
        db = con.statboard
    return db.socialmedia


def get_oauth():
    oauth = OAuth1(api_setup.tw_consumer_key,
                   client_secret=api_setup.tw_consumer_secret,
                   resource_owner_key=api_setup.tw_oauth_token,
                   resource_owner_secret=api_setup.tw_oauth_token_secret
                   )
    return oauth


def get_social_media_data():
    try:
        # on heroku
        client = MongoClient(environ['MONGOLAB_URI'])
        db = client.get_default_database()
    except (ConnectionFailure, KeyError, NameError):
        # locally
        con = Connection()
        db = con.statboard
    return db.socialmedia


def get_oauth():
    oauth = OAuth1(api_setup.tw_consumer_key,
                   client_secret=api_setup.tw_consumer_secret,
                   resource_owner_key=api_setup.tw_oauth_token,
                   resource_owner_secret=api_setup.tw_oauth_token_secret
                   )
    return oauth


def instagram_counts():
    sm = get_social_media_data()
    for instauser in config.instagram_users:
        r = requests.get(
            'https://api.instagram.com/v1/users/%s/?client_id=%s'
            % (instauser['id'], api_setup.ig_client_id)
        )
        r = r.json()
        insert = {
            "service": "instagram",
            "user_account": instauser['user'],
            "datetime": int(time()),
            "followers": r['data']['counts']['followed_by']
        }
        sm.insert(insert)
        send_message(insert)

    print "Instagram Imported."


def twitter_counts():
    oauth = get_oauth()
    sm = get_social_media_data()
    for twitteruser in config.twitter_users:
        r = requests.get(
            url="https://api.twitter.com/1.1/users/lookup.json?screen_name=%s" % twitteruser['user'],
            auth=oauth)
        r = r.json()
        insert = {
            'service': 'twitter',
            'user_account': twitteruser['user'],
            'datetime': int(time()),
            'followers': int(r[0]['followers_count'])
        }
        sm.insert(insert)
        send_message(insert)
    print "Twitter Imported."


class TemplateRendering:

    def render_template(self, template_name, variables):
        template_dirs = []
        # added a default for fail over.
        template_dirs.append(path.join(path.dirname(__file__), 'templates'))

        env = Environment(loader=FileSystemLoader(template_dirs))

        try:
            template = env.get_template(template_name)
        except TemplateNotFound:
            raise TemplateNotFound(template_name)
        content = template.render(variables)
        return content


class IndexHandler(tornado.web.RequestHandler, TemplateRendering):
    def get(self):
        data = {}
        sm = get_social_media_data()
        data['vamuseum'] = sm.find({"user_account": "vamuseum"}).limit(2000)
        data['instaspark'] = []
        data['twitterspark'] = []
        for user in config.instagram_users:
            data['instaspark'].append({
                'name': user['name'],
                'data': sm.find({"user_account": user['user']})
                          .sort("_id", -1)
                          .limit(40)
            })
        for user in config.twitter_users:
            data['twitterspark'].append({
                'name': user['name'],
                'data': sm.find({"user_account": user['user']})
                          .sort("_id", -1)
                          .limit(40)
            })

        content = self.render_template('index.html', data)
        self.write(content)


class WebSocketHandler(websocket.WebSocketHandler):
    def open(self, *args):
        clients.append(self)
        print "New web socket connection: %s" % self


def send_message(message=None):

    if not message:
        message = {"followers": random.randrange(17950,17960), "user_account": "vamuseum", "service": "instagram", "datetime": int(time())}

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



app = tornado.web.Application([
    (r'/', IndexHandler),
    (r'/assets/(.*)', tornado.web.StaticFileHandler, {'path': './assets'},),
    (r'/ws/', WebSocketHandler),
])

if __name__ == '__main__':
    parse_command_line()
    app.listen(options.port)

    sched = Scheduler(daemon=True)
    atexit.register(lambda: sched.shutdown())
    sched.add_cron_job(instagram_counts, minute="*/1")
    sched.add_cron_job(twitter_counts, minute="*/1")
    #sched.add_cron_job(send_message, second="*/30")
    sched.start()

    tornado.ioloop.IOLoop.instance().start()