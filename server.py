import atexit
from os import path, environ
from time import time

import requests
from requests_oauthlib import OAuth1

import tornado.ioloop
import tornado.web
import config
import api_setup

from apscheduler.scheduler import Scheduler
from pymongo import Connection, MongoClient
from pymongo.errors import ConnectionFailure
from tornado.options import define, options, parse_command_line
from jinja2 import Environment, FileSystemLoader, TemplateNotFound


define("port", default=8080, help="run on the given port", type=int)

clients = []

sched = Scheduler()

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
        resource_owner_secret=api_setup.tw_oauth_token_secret)
    return oauth

class TemplateRendering:
    """TemplateRendering
       A simple class to hold methods for rendering templates.
    """

    def render_template(self, template_name, variables):
        """render_template
            Returns the result of template.render to be used elsewhere.
            I think this will be useful to render templates to be passed into other templates.
            Gets the template directory from app settings dictionary with a fall back to "templates" as a default.
            Probably could use a default output if a template isn't found instead of throwing an exception.
        """
        template_dirs = []
        template_dirs.append(path.join(path.dirname(__file__), 'templates')) # added a default for fail over.

        env = Environment(loader = FileSystemLoader(template_dirs))

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


def instagram_counts(filter=None):
    sm = get_social_media_data()
    # for stat in sm.find():
    #     sm.remove(stat)
    for instauser in config.instagram_users:
        r = requests.get(
            'https://api.instagram.com/v1/users/%s/?client_id=%s'
            % (instauser['id'], api_setup.ig_client_id)
        )
        r = r.json()
        insert = {
            'service': 'instagram',
            'user_account': instauser['user'],
            'datetime': int(time()),
            'followers': r['data']['counts']['followed_by']
        }
        sm.insert(insert)
    print "Instagram Imported."


def twitter_counts(filter=None):
    oauth = get_oauth()
    sm = get_social_media_data()
    # for stat in sm.find():
    #     sm.remove(stat)
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
    print "Twitter Imported."


class Collector(tornado.web.RequestHandler):
    def get(self, filter):
        twitter_counts()


class EventSchedule(tornado.web.RequestHandler):
    def get(self):
        sched.print_jobs()

handlers = tornado.web.Application([
    (r'/', IndexHandler),
    (r'/collect/(.*)', Collector),
    (r'/schedule', EventSchedule),
])


if __name__ == '__main__':
    parse_command_line()
    handlers.listen(options.port)

    sched = Scheduler(daemon=True)
    atexit.register(lambda: sched.shutdown())
    sched.add_cron_job(instagram_counts, minute="*/5")
    sched.add_cron_job(twitter_counts, minute="*/5")
    # sched.add_cron_job(instagram_counts, minute="*/5", args=['blah'])
    sched.start()

    tornado.ioloop.IOLoop.instance().start()