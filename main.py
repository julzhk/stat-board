import config
import atexit
from apscheduler.scheduler import Scheduler
import json
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from os import path, environ
from time import gmtime, strftime, time
import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.httpserver
from tornado.websocket import WebSocketClosedError
from tornado.options import define, options, parse_command_line
from pymongo import Connection, MongoClient
import requests
from requests_oauthlib import OAuth1
import random

define("port", default=8080, help="run on the given port", type=int)

# List of all the clients connected via websockets
clients = []
sched = Scheduler()


def get_social_media_data():
    try:
        client = MongoClient(environ['MONGOLAB_URI'])
        db = client.get_default_database()
    except:
        con = Connection()
        db = con.statboard
    return db.socialmedia


def get_oauth():
    oauth = OAuth1(environ['TWITTER_CONSUMER_KEY'],
                   client_secret=environ['TWITTER_CONSUMER_SECRET'],
                   resource_owner_key=environ['TWITTER_OAUTH_TOKEN'],
                   resource_owner_secret=environ['TWITTER_OAUTH_TOKEN_SECRET']
                   )
    return oauth

def instagram_counts():
    sm = get_social_media_data()
    for instauser in config.INSTAGRAM_USERS:
        r = requests.get(
            'https://api.instagram.com/v1/users/%s/?client_id=%s'
            % (instauser['id'], environ['INSTAGRAM_CLIENT_ID'])
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
    for twitteruser in config.TWITTER_USERS:
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


def pinterest_counts():
    '''
    Key point: At time of writing the Pinterest API is unofficial and may/will vanish without notice
    '''
    sm = get_social_media_data()
    for pinterest_user in config.PINTEREST_USERS:
        r = requests.get(
            url="https://api.pinterest.com/v3/pidgets/users/%s/pins/" % pinterest_user['user']
        )
        r = r.json()
        insert = {
            'service': 'pinterest',
            'user_account': pinterest_user['user'],
            'datetime': int(time()),
            'followers': int(r['data']['user']['follower_count'])
        }
        sm.insert(insert)
        send_message(insert)
    print "Pinterest Imported."


class TemplateRendering:

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
    def get(self):
        data = {}
        sm = get_social_media_data()
        data['vamuseum'] = sm.find({"user_account": "vamuseum"}).limit(2000)
        data['instaspark'] = []
        data['twitterspark'] = []
        data['pinterestspark'] = []
        data['host'] = self.request.host
        for user in config.INSTAGRAM_USERS:
            data['instaspark'].append({
                'name': user['name'],
                'data': sm.find({"user_account": user['user'], "service": 'instagram'})
                          .sort("_id", -1)
                          .limit(40)
            })
        for user in config.TWITTER_USERS:
            data['twitterspark'].append({
                'name': user['name'],
                'data': sm.find({"user_account": user['user'], "service": 'twitter'})
                          .sort("_id", -1)
                          .limit(40)
            })
        for user in config.PINTEREST_USERS:
            data['pinterestspark'].append({
                'name': user['name'],
                'data': sm.find({"user_account": user['user'], "service": 'pinterest'})
                          .sort("_id", -1)
                          .limit(40)
            })

        content = self.render_template('index.html', data)
        self.write(content)


class WebSocketHandler(tornado.websocket.WebSocketHandler):
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


def main():

    application = tornado.web.Application([
        (r'/', IndexHandler),
        (r'/test', TestHandler),
        (r'/assets/(.*)', tornado.web.StaticFileHandler, {'path': './assets'},),
        (r'/ws/', WebSocketHandler)
    ])

    parse_command_line()
    application.listen(options.port)

    sched = Scheduler(daemon=True)
    atexit.register(lambda: sched.shutdown())
    sched.add_cron_job(instagram_counts, minute="*/1")
    sched.add_cron_job(twitter_counts, minute="*/1")
    sched.add_cron_job(pinterest_counts, minute="*/5")
    sched.start()

    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
