import httplib2
from apiclient.discovery import build
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run
from oauth2client.client import AccessTokenRefreshError
from apiclient.errors import HttpError
CLIENT_SECRETS = 'client_secrets.json'
MISSING_CLIENT_SECRETS_MESSAGE = '%s is missing' % CLIENT_SECRETS
TOKEN_FILE_NAME = 'analytics.dat'
# The Flow object to be used if we need to authenticate.
FLOW = flow_from_clientsecrets(CLIENT_SECRETS,
                               scope='https://www.googleapis.com/auth/analytics.readonly',
                               message=MISSING_CLIENT_SECRETS_MESSAGE)


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
        firstAccountId = accounts.get('items')[n].get('id')
        webproperties = service.management().webproperties().list(
            accountId=firstAccountId).execute()
        if webproperties.get('items'):
            firstWebpropertyId = webproperties.get('items')[0].get('id')
            profiles = service.management().profiles().list(
                accountId=firstAccountId,
                webPropertyId=firstWebpropertyId).execute()
            if profiles.get('items'):
                return profiles.get('items')[0].get('id')
    return None


def get_results(service, profile_id):
    # Use the Analytics Service Object to query the Core Reporting API
    return service.data().ga().get(
        ids='ga:' + profile_id,
        start_date='2014-06-24',
        end_date='2014-07-24',
        metrics='ga:sessions').execute()


def print_results(results):
    if results:
        print 'First View (Profile): %s' % results.get('profileInfo').get('profileName')
        print 'Total Sessions: %s' % results.get('rows')[0][0]

    else:
        print 'No results found'


if __name__ == '__main__':
    service = initialize_service()
    try:
        profile_id = get_first_profile_id(service)
        if profile_id:
            results = get_results(service, profile_id)
            print_results(results)
    except TypeError, error:
        print ('There was an error in constructing your query : %s' % error)
    except HttpError, error:
        print ('Arg, there was an API error : %s : %s' %
               (error.resp.status, error._get_reason()))
    except AccessTokenRefreshError:
        print ('The credentials have been revoked or expired, please re-authorize')