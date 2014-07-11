import config
from os import environ

try:
    instagram_client_id = environ['instagram_client_id']
    instagram_client_src = environ['instagram_client_src']
except (KeyError):
    ig_client_id = config.instagram_client_id
    ig_client_src = config.instagram_client_src