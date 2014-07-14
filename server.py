import atexit
from os import path
from time import time

import requests

import tornado.ioloop
import tornado.web
import config
import api_setup

from lib import map_elements_for_chart
from apscheduler.scheduler import Scheduler
from pymongo import Connection
from pymongo.errors import (AutoReconnect,
                            ConfigurationError,
                            ConnectionFailure,
                            DocumentTooLarge,
                            DuplicateKeyError,
                            InvalidURI,
                            OperationFailure)
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
    except ConnectionFailure:
        # locally
        con = Connection()
        db = con.statboard
    return db.socialmedia


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
        for instauser in config.instagram_users:
            data['instaspark'].append({
                'name': instauser['name'],
                'data': sm.find({"user_account": instauser['user']})
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


class Collector(tornado.web.RequestHandler):
    def get(self, filter):
        instagram_counts()


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
    # sched.add_cron_job(instagram_counts, minute="*/5", args=['blah'])
    sched.start()

    tornado.ioloop.IOLoop.instance().start()