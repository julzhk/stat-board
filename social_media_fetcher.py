import config
from os import environ
from pymongo import Connection, MongoClient
import requests
from requests_oauthlib import OAuth1
from time import time

def get_social_media_data():
    try:
        client = MongoClient(environ['MONGOLAB_URI'])
        db = client.get_default_database()
    except:
        con = Connection()
        db = con.statboard
    return db.socialmedia


def insert_to_mongo(insert):
    sm = get_social_media_data()
    sm.insert(insert)


def request_social_json(url):
    r = requests.get(url)
    return r.json()


def instagram_counts():
    for user in config.INSTAGRAM_USERS:
        url = 'https://api.instagram.com/v1/users/%s/?client_id=%s' % (user['id'], environ['INSTAGRAM_CLIENT_ID'])
        r = request_social_json(url)
        insert = {
            "service": "instagram",
            "user_account": user['user'],
            "datetime": int(time()),
            "followers": r['data']['counts']['followed_by']
        }
        insert_to_mongo(insert)
        # send_message(insert)
    print "Instagram Imported."


def facebook_counts():
    for user in config.FACEBOOK_PAGE:
        url = "http://graph.facebook.com/%s/" % user['id']
        r = request_social_json(url)
        insert = {
            'service': 'facebook',
            'user_account': user['user'],
            'datetime': int(time()),
            'followers': int(r['likes'])
        }
        insert_to_mongo(insert)
        # send_message(insert)
    print "Facebook Imported."



def twitter_counts():
    oauth = OAuth1(environ['TWITTER_CONSUMER_KEY'],
                   client_secret=environ['TWITTER_CONSUMER_SECRET'],
                   resource_owner_key=environ['TWITTER_OAUTH_TOKEN'],
                   resource_owner_secret=environ['TWITTER_OAUTH_TOKEN_SECRET']
                   )

    for user in config.TWITTER_USERS:
        r = requests.get(
            url="https://api.twitter.com/1.1/users/lookup.json?screen_name=%s" % user['user'],
            auth=oauth)
        r = r.json()
        insert = {
            'service': 'twitter',
            'user_account': user['user'],
            'datetime': int(time()),
            'followers': int(r[0]['followers_count'])
        }
        insert_to_mongo(insert)
        # send_message(insert)
    print "Twitter Imported."


def linkedin_count():
    oauth = OAuth1(environ['LINKEDIN_API_KEY'],
                   client_secret=environ['LINKEDIN_SECRET_KEY'],
                   resource_owner_key=environ['LINKEDIN_OAUTH_TOKEN'],
                   resource_owner_secret=environ['LINKEDIN_OAUTH_TOKEN_SECRET']
                   )


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
        insert_to_mongo(insert)
        # send_message(insert)
    print "LinkedIn Imported."


def pinterest_counts():
    '''
    Key point: At time of writing the Pinterest API is unofficial and may/will vanish without notice
    '''
    for user in config.PINTEREST_USERS:
        url = "https://api.pinterest.com/v3/pidgets/users/%s/pins/" % user['user']
        r = request_social_json(url)
        insert = {
            'service': 'pinterest',
            'user_account': user['user'],
            'datetime': int(time()),
            'followers': int(r['data']['user']['follower_count'])
        }
        insert_to_mongo(insert)
        # send_message(insert)
    print "Pinterest Imported."


def youtube_counts():
    for user in config.YOUTUBE_USERS:
        url = "http://gdata.youtube.com/feeds/api/users/%s?v=2&alt=json" % user['user']
        r = request_social_json(url)
        insert = {
            'service': 'youtube',
            'user_account': user['user'],
            'datetime': int(time()),
            'followers': int(r['entry']['yt$statistics']['subscriberCount'])
        }
        insert_to_mongo(insert)
        # send_message(insert)
    print "YouTube Imported."