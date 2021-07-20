from __future__ import print_function
import os.path
import json
import time
import re

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from databases import Database as DB
from apiclient import errors
from timing import timing

# Provies Google API utilility functions
class driveUtils:
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets' , 'https://www.googleapis.com/auth/drive']
    creds = None
    user_info = None

    def updateToken(self):
        #gets tokens from credential info
        if self.creds is None:
            if not self.creds:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', self.SCOPES)
                creds = flow.run_local_server(port=0)
            # save creds
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

    def is_creds_expired(self):
        if os.path.exists('token.json'):
            with open('token.json') as file:
                token_info = json.load(file)
            expiry = token_info['expiry']
            exp_date = re.search(r'([0-9]*)-([0-9]+)-([0-9]+)T([0-9]+):([0-9]+):([0-9]+).',expiry)
            #checks if credentials have expired
            expired = timing.has_exp(int(exp_date.group(1)), int(exp_date.group(2)), int(exp_date.group(3)), int(exp_date.group(4)), int(exp_date.group(5)), int(exp_date.group(6)), 5)
            return expired
        else:
            print('token.json does not exist')
            return None

    def get_creds(self):
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', self.SCOPES)
            return 0
        else:
            return None

    def load_user_info(self):
        if os.path.exists('user_info.json'):
            with open('user_info.json') as file:
                self.user_info = json.load(file)
                return 0
        else:
            print('missing user_info')
            return None

    def updateDirectory(self):
        if self.creds is None:
            print('loading credentials')
            self.get_creds()
        if self.is_creds_expired():
            print('expired credentials')
            return None

        #print(user_info)
        SPREADSHEET_ID = self.user_info['spreadsheetid']
        PARENT_ID = self.user_info['parentid']

        SAMPLE_RANGE_NAME = 'Class Data!A1:E'

        # find what next line to add to - get sheets
        service_sheets = build('sheets', 'v4', credentials=self.creds)

        #list of ids for drive files
        
        ids = []
        #loop specific stuff
        isFinished = False
        maxIndex = 10000
        minIndex = 2
        
        while not isFinished:
            result = service_sheets.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID, range = ("A{}:F{}".format(minIndex, maxIndex))).execute()
            rows = result.get('values', [])
            isFinished = len(result) < maxIndex/2
            if not isFinished:
                maxIndex += 10000
            
            for row in rows:
                if(len(row) >= 5 and len(row[4]) > 5):
                    ids.append(re.split(r'.+\/(.*)\/view', row[4] )[1])

        # Get files
        service_drive = build('drive', 'v3', credentials=self.creds)
        page_token = None
        entries = []
        links = []
        while True:
            response = service_drive.files().list(q="'{}' in parents".format(PARENT_ID),
                                                spaces='drive',
                                                fields='nextPageToken, files(id, name)',
                                                pageToken=page_token).execute()
            for file in response.get('files', []):
                # get entries & parse
                if not (file.get('id') in ids):
                    entries.append(file.get('name').split('&'))
                    links.append("https://drive.google.com/file/d/{}/view".format(file.get('id')))

                #check if entry has already been added
            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break

        link_index = 0
        link_i_max = len(links)-1
        for i in range(0, len(entries), 1):
            # incase user ommitted certain categories, find number of entries
            under_count = 5 - len(entries[i])
            if under_count > 0:
                for j in range(0, under_count):
                    entries[i].append('-')
            entries[i] = entries[i][0:4:1]
            if(link_index <= link_i_max):
                entries[i].append(links[link_index])
                link_index+=1
        
        # add to line(s)
        values = [
            entries
        ]
        body = {
            'values' : entries
        }
        result = service_sheets.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID, range="A{}:F{}".format(len(rows)+2,len(entries)+len(rows)+1),
        valueInputOption = "USER_ENTERED", body=body).execute()
        print(entries)