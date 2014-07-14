import config
from os import environ

try:
    ig_client_id = environ['instagram_client_id']
    ig_client_id = environ['instagram_client_src']
except (KeyError):
    ig_client_id = config.instagram_client_id
    ig_client_src = config.instagram_client_src


try:
    tw_request_token_url = environ['twitter_request_token_url']
    tw_authorise_url = environ['twitter_authorise_url']
    tw_access_token_url = environ['twitter_access_token_url']
    tw_consumer_key = environ['twitter_consumer_key']
    tw_consumer_secret = environ['twitter_consumer_secret']
    tw_oauth_token = environ['twitter_oauth_token']
    tw_oauth_token_secret = environ['twitter_oauth_token_secret']
except (KeyError):
    tw_request_token_url = config.twitter_request_token_url
    tw_authorise_url = config.twitter_authorise_url
    tw_access_token_url = config.twitter_access_token_url
    tw_consumer_key = config.twitter_consumer_key
    tw_consumer_secret = config.twitter_consumer_secret
    tw_oauth_token = config.twitter_oauth_token
    tw_oauth_token_secret = config.twitter_oauth_token_secret