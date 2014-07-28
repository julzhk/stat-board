from collections import OrderedDict
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


def facebook_counts():
    sm = get_social_media_data()
    for face_user in config.FACEBOOK_PAGE:
        r = requests.get(
            url="http://graph.facebook.com/%s/" % face_user['id']
        )
        r = r.json()
        insert = {
            'service': 'facebook',
            'user_account': face_user['user'],
            'datetime': int(time()),
            'followers': int(r['likes'])
        }
        sm.insert(insert)
        send_message(insert)
    print "Facebook Imported."


def twitter_counts():
    oauth = OAuth1(environ['TWITTER_CONSUMER_KEY'],
                   client_secret=environ['TWITTER_CONSUMER_SECRET'],
                   resource_owner_key=environ['TWITTER_OAUTH_TOKEN'],
                   resource_owner_secret=environ['TWITTER_OAUTH_TOKEN_SECRET']
                   )

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


def linkedin_count():
    oauth = OAuth1(environ['LINKEDIN_API_KEY'],
                   client_secret=environ['LINKEDIN_SECRET_KEY'],
                   resource_owner_key=environ['LINKEDIN_OAUTH_TOKEN'],
                   resource_owner_secret=environ['LINKEDIN_OAUTH_TOKEN_SECRET']
                   )

    sm = get_social_media_data()
    for user in config.LINKEDIN_USERS:
        r = requests.get(
            url="http://api.linkedin.com/v1/companies/%s:(num-followers)?format=json" % user['id'],
            auth=oauth)
        r = r.json()
        insert = {
            'service': 'linkedin',
            'user_account': user['user'],
            'datetime': int(time()),
            'followers': int(r['numFollowers'])
        }
        sm.insert(insert)
        send_message(insert)
    print "LinkedIn Imported."


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


def youtube_counts():
    sm = get_social_media_data()
    for user in config.YOUTUBE_USERS:
        r = requests.get(
            url="http://gdata.youtube.com/feeds/api/users/%s?v=2&alt=json" % user['user']
        )
        r = r.json()
        insert = {
            'service': 'youtube',
            'user_account': user['user'],
            'datetime': int(time()),
            'followers': int(r['entry']['yt$statistics']['subscriberCount'])
        }
        sm.insert(insert)
        send_message(insert)
    print "YouTube Imported."


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
        data['instaspark'] = []
        data['twitterspark'] = []
        data['pinterestspark'] = []
        data['facebookspark'] = []
        data['youtubespark'] = []
        data['linkedinspark'] = []
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
        for user in config.FACEBOOK_PAGE:
            data['facebookspark'].append({
                'name': user['name'],
                'data': sm.find({"user_account": user['user'], "service": 'facebook'})
                          .sort("_id", -1)
                          .limit(40)
            })
        for user in config.YOUTUBE_USERS:
            data['youtubespark'].append({
                'name': user['name'],
                'data': sm.find({"user_account": user['user'], "service": 'youtube'})
                          .sort("_id", -1)
                          .limit(40)
            })
        for user in config.LINKEDIN_USERS:
            data['linkedinspark'].append({
                'name': user['name'],
                'data': sm.find({"user_account": user['user'], "service": 'linkedin'})
                          .sort("_id", -1)
                          .limit(40)
            })

        content = self.render_template('index.html', data)
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

        content = self.render_template('dash.html', data)
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
        (r'/dash', DashHandler),
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
    sched.add_cron_job(youtube_counts, minute="*/5")
    sched.add_cron_job(facebook_counts, minute="*/1")
    sched.add_cron_job(linkedin_count, minute="*/5")
    sched.start()

    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
