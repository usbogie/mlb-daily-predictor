from __future__ import print_function
import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/sheets.googleapis.com-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Google Sheets API Python Quickstart'


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'sheets.googleapis.com-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        credentials = tools.run_flow(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def update_spreadsheet(data):
    """
    target_doc
    https://docs.google.com/spreadsheets/d/1rS_7hitA1ZNzZsDcYqIKl621hvYuO5s63sSNlpu6ZHM/edit
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discoveryUrl)

    spreadsheet_Id = '1rS_7hitA1ZNzZsDcYqIKl621hvYuO5s63sSNlpu6ZHM'
    rangeAll = 'A2:U'
    body = {}
    resultClear = service.spreadsheets().values().clear(
        spreadsheetId=spreadsheet_Id, range=rangeAll, body=body).execute()
    rangeName = 'A2:U'
    headers = ['Lineup status','ML','Projected ML','ML value %','RL',
               'Projected RL', 'RL value %','Total/odds','Avg total/Over %',
               'Over/under value %','F5 ML','F5 projected ML','F5 ML value %',
               'F5 RL','F5 Projected RL','F5 RL value %','F5 Total',
               'F5 avg total/Over %','F5 over value','Score in 1st yes/no']
    all_rows = []
    for game in data:
        values_space = [""]*21
        values0 = [game[0]] + headers
        values1 = list(game[1].values())
        values2 = list(game[2].values())
        all_rows.extend([values_space,values0,values1,values2])
    body = {
        'values': all_rows
    }
    result = service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_Id, range=rangeName,
        valueInputOption='RAW', body=body).execute()
    print('{0} cells updated.'.format(result.get('updatedCells')))


if __name__ == '__main__':
    update_spreadsheet()
