from __future__ import print_function
import os.path
import json
import time
import re

#code for oauth stuff
from google.oauth2 import service_account

import googleapiclient.discovery
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from databases import Database as DB
from apiclient import errors
from timing import timing

# Provies Google API utilility functions
class driveUtils:
    #CONSTS
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets' , 'https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/sqlservice.admin']
    SERVICE_ACCOUNT_FILE = None
    SHEETS_INFO_FILE = None
    SPREADSHEET_ID = None
    PARENT_ID = None

    credentials = None
    delegated_credentials = None
    user_info = None
    service_sheets = None
    service_drive = None

    
    def __init__(self, creds_path = 'creds.json', sheets_path = "user_info.json" ):
        self.SERVICE_ACCOUNT_FILE = creds_path
        self.SHEETS_INFO_FILE = sheets_path
        self.init_creds()
        self.load_user_info()

    def init_creds(self):
        if not os.path.exists(self.SERVICE_ACCOUNT_FILE):
            print('Missing credentials file')
        else:
            try:
                self.credentials = service_account.Credentials.from_service_account_file( self.SERVICE_ACCOUNT_FILE, scopes=self.SCOPES)
                self.delegated_credentials = self.credentials.with_subject('automated-acct@rocket-receipt.iam.gserviceaccount.com')
                print("creds loaded")
            except:
                print("something went wrong with validating credentials")

    def load_user_info(self):
        if not os.path.exists(self.SHEETS_INFO_FILE):
            print('missing user info file')
        else:
            try:
                with open(self.SHEETS_INFO_FILE) as file:
                    self.user_info = json.load(file)
                self.SPREADSHEET_ID = self.user_info['spreadsheetid']
                self.PARENT_ID = self.user_info['driveid']
                print("ID's loaded")
            except: 
                print("problem encountered loading user info")


    def updateDirectory(self):
        SAMPLE_RANGE_NAME = 'Class Data!A1:E'

        # find what next line to add to - get sheets
        self.service_sheets = build('sheets', 'v4', credentials = self.credentials )
        '''
        try:
            self.service_sheets = build('sheets', 'v4', credentials=self.delegated_credentials)
        except:
            print('sheets service failed to build')
        '''

        #list of ids for drive files
        ids = []
        #loop specific stuff
        isFinished = False
        maxIndex = 10000
        minIndex = 2
        
        while not isFinished:
            result = None
            result = self.service_sheets.spreadsheets().values().get( spreadsheetId = self.SPREADSHEET_ID, range = ("A{}:F{}".format(minIndex, maxIndex))).execute()
            try:
                result = self.service_sheets.spreadsheets().values().get( 
                    spreadsheetId = self.SPREADSHEET_ID, range = ("A{}:F{}".format(minIndex, maxIndex))).execute()
            except:
                print("failed to get spread sheet values")
                return

            print(result)
            rows = result.get('values', [])
            isFinished = len(result) < maxIndex/2
            if not isFinished:
                maxIndex += 10000
            
            for row in rows:
                if(len(row) >= 5 and len(row[4]) > 5):
                    ids.append(re.split(r'.+\/(.*)\/view', row[4] )[1])

        # Get files
        try:
            self.service_drive = build('drive', 'v3', credentials=self.credentials)
        except:
            print('failed to build google drive service')
            return
        page_token = None
        entries = []
        links = []
        while True:
            try:
                response = self.service_drive.files().list(q="'{}' in parents".format(self.PARENT_ID),
                                                    spaces='drive',
                                                    fields='nextPageToken, files(id, name)',
                                                    pageToken=page_token).execute()
            except:
                print('failed to get drive data')
                return

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
        
        result = self.service_sheets.spreadsheets().values().update( 
        spreadsheetId = self.SPREADSHEET_ID, range="A{}:F{}".format(len(rows)+2,len(entries)+len(rows)+1),
        valueInputOption = "USER_ENTERED", body=body).execute()
        #print(entries)