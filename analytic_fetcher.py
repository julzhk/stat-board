import httplib2
from os import environ
from apiclient.discovery import build
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run
from oauth2client.client import AccessTokenRefreshError
from apiclient.errors import HttpError
from datetime import datetime, timedelta
from calendar import timegm
from pymongo import Connection, MongoClient

CLIENT_SECRETS = 'analytics/client_secrets.json'
MISSING_CLIENT_SECRETS_MESSAGE = '%s is missing' % CLIENT_SECRETS
TOKEN_FILE_NAME = 'analytics/analytics.dat'
# The Flow object to be used if we need to authenticate.
FLOW = flow_from_clientsecrets(CLIENT_SECRETS,
                               scope='https://www.googleapis.com/auth/analytics.readonly',
                               message=MISSING_CLIENT_SECRETS_MESSAGE)


def setup_mongo():
    try:
        client = MongoClient(environ['MONGOLAB_URI'])
        db = client.get_default_database()
    except:
        con = Connection()
        db = con.statboard
    return db.socialmedia


def prepare_credentials():
    storage = Storage(TOKEN_FILE_NAME)
    credentials = storage.get()
    if credentials is None or credentials.invalid:
        credentials = run(FLOW, storage)  # run Auth Flow and store credentials
    return credentials


def initialize_service():
    http = httplib2.Http()
    credentials = prepare_credentials()
    http = credentials.authorize(http)  # authorize the http object
    return build('analytics', 'v3', http=http)


def get_results(start_date=None, end_date=None):

    if start_date is None:
        start_date = datetime.now() - timedelta(days=1)

    if end_date is None:
        end_date = start_date

    service = initialize_service()
    profile_id = '595561'

    try:
        results = service.data().ga().get(
            ids='ga:' + profile_id,
            start_date=str(start_date.date()),
            end_date=str(end_date.date()),
            metrics='ga:sessions,ga:users,ga:pageviews,ga:pageviewsPerSession',
            dimensions='ga:date').execute()

    except TypeError, error:
        print ('There was an error in constructing your query : %s' % error)
    except HttpError, error:
        print ('Arg, there was an API error : %s : %s' %
               (error.resp.status, error._get_reason()))
    except AccessTokenRefreshError:
        print ('The credentials have been revoked or expired, please re-authorize')

    results_to_mongo(results)

def backfill_results(days=10):
    '''
    Selects  data from the last [days]
    '''
    start_date = datetime.now() - timedelta(days=days)
    end_date = datetime.now() - timedelta(days=1)

    return get_results(start_date, end_date)


def results_to_mongo(results):
    sm = setup_mongo()
    for result in results['rows']:
        date = datetime.strptime(result[0], '%Y%m%d')
        insert = {
            'service': 'analytic_overview',
            'date': timegm(date.utctimetuple()),
            'profile_id': results.get('profileInfo').get('profileId'),
            'sessions': result[1],
            'users': result[2],
            'pageviews': result[3],
            'pageviews_per_session': result[4]
        }
        sm.insert(insert)


def go_get():
    results = get_results()
    print results
    # results_to_mongo(results)


if __name__ == '__main__':
   go_get()