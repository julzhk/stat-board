import httplib2
from apiclient.discovery import build
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run
from oauth2client.client import AccessTokenRefreshError
from apiclient.errors import HttpError
from pprint import pprint
from datetime import datetime
from calendar import timegm
from pymongo import Connection, MongoClient
CLIENT_SECRETS = 'analytics/client_secrets.json'
MISSING_CLIENT_SECRETS_MESSAGE = '%s is missing' % CLIENT_SECRETS
TOKEN_FILE_NAME = 'analytics.dat'
# The Flow object to be used if we need to authenticate.
FLOW = flow_from_clientsecrets(CLIENT_SECRETS,
                               scope='https://www.googleapis.com/auth/analytics.readonly',
                               message=MISSING_CLIENT_SECRETS_MESSAGE)

def get_social_media_data():
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


def get_first_profile_id(service):
    return get_nth_profile_id(service=service, n=0)


def get_nth_profile_id(service, n=0):
    """
    Returns:
      A string with the first profile ID. None if a user does not have any
      accounts, webproperties, or profiles.
    """
    accounts = service.management().accounts().list().execute()
    if accounts.get('items'):
        Nth_AccountId = accounts.get('items')[n].get('id')
        webproperties = service.management().webproperties().list(
            accountId=Nth_AccountId).execute()
        if webproperties.get('items'):
            firstWebpropertyId = webproperties.get('items')[0].get('id')
            profiles = service.management().profiles().list(
                accountId=Nth_AccountId,
                webPropertyId=firstWebpropertyId).execute()
            if profiles.get('items'):
                return profiles.get('items')[0].get('id')
    return None


def get_results(service, profile_id):
    # Use the Analytics Service Object to query the Core Reporting API
    return service.data().ga().get(
        ids='ga:' + profile_id,
        start_date='2014-07-24',
        end_date='2014-07-24',
        metrics='ga:sessions,ga:users,ga:pageviews,ga:pageviewsPerSession').execute()


def top_pages(service, profile_id, start_date = '2014-07-01', end_date = '2014-08-13',max_results = 10):
    """
    # Use the Analytics Service Object to query the Core Reporting API
    refs:

    https://developers.google.com/analytics/devguides/reporting/core/v3/common-queries

    http://ga-dev-tools.appspot.com/explorer/?dimensions=
    ga%253ApagePath&metrics=ga%253Apageviews%252Cga%253AuniquePageviews
    %252Cga%253AtimeOnPage%252Cga%253Abounces%252Cga%253Aentrances%252Cga%253Aexits&
    sort=-ga%253Apageviews
    """

    return service.data().ga().get(
        ids='ga:' + profile_id,
        start_date=('%s' % start_date),
        end_date=end_date,
        max_results = max_results,
        dimensions='ga:pagePath',
        metrics='ga:pageviews,ga:uniquePageviews,ga:timeOnPage,ga:bounces,ga:entrances,ga:exits',
        sort='-ga:pageviews').execute()


def insert_results_into_mongo(results):
    sm = get_social_media_data()
    date = datetime.strptime(results.get('query').get('start-date'), '%Y-%m-%d')
    r = {
        'service': 'analytic_overview',
        'date': timegm(date.utctimetuple()),
        'profile_id': results.get('profileInfo').get('profileId'),
        'sessions': results.get('totalsForAllResults').get('ga:sessions'),
        'users': results.get('totalsForAllResults').get('ga:users'),
        'pageviews': results.get('totalsForAllResults').get('ga:pageviews'),
        'pageviews_per_session': results.get('totalsForAllResults').get('ga:pageviewsPerSession')
    }
    sm.insert(r)
    return r


def get_top_pages():
    service = initialize_service()
    results = {}
    try:
        #profile_id = get_first_profile_id(service)
        profile_id = '595561'
        if profile_id:
            results = top_pages(service, profile_id)

    except TypeError, error:
        print ('There was an error in constructing your query : %s' % error)
    except HttpError, error:
        print ('Arg, there was an API error : %s : %s' %
               (error.resp.status, error._get_reason()))
    except AccessTokenRefreshError:
        print ('The credentials have been revoked or expired, please re-authorize')
    # insert_results_into_mongo(results)
    # return just the paths
    return [r[0] for r in results['rows']]

if __name__ == '__main__':
    r = get_top_pages()
    pprint(r)