import os
import re
import sys
import json
import pickle
from notion_client import Client
from datetime import timedelta, date
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow


# Get the absolute path to the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the absolute file paths within the container
FILEPATH = os.path.join(current_dir, "../token/notion_setting.json")
CLIENTPATH = os.path.join(current_dir, "../token/client_secret.json")
CREDPATH = os.path.join(current_dir, "../token/token.pkl")


class Notion():
    def __init__(self):
        if os.path.exists(FILEPATH):
            with open(FILEPATH) as f:
                data = json.load(f)
        else:
            print("Make sure you store notion_setting.json in toke folder")
        # open up a task and then copy the URL root up to the "p="
        self.URLROOT = data["urlroot"]
        print(f"--- urlroot: {self.URLROOT} is setting ---")
        self.DATABASE_ID = self.get_database_id(data["urlroot"])
        print(f"--- database_id: {self.DATABASE_ID} is setting ---")
        # Change timecode to be representative of your timezone, it has to be adjusted as daylight savings
        self.TIMECODE = data["timecode"]
        print(f"--- timecode: {self.TIMECODE} is setting ---")
        self.TIMEZONE = data["timezone"]
        print(f"--- timezone: {self.TIMEZONE} is setting ---")
        # Notion search range: go back to which date?
        # google search range: go back to which date?
        self.AFTER_DATE = (date.today() + timedelta(days=-
                           data["goback_days"])).strftime(f"%Y-%m-%d")
        print(f"--- goback_days: {self.AFTER_DATE} is setting ---")
        self.BEFORE_DATE = (
            date.today() + timedelta(days=+ data["goforward_days"])).strftime(f"%Y-%m-%d")
        print(f"--- goforward_days: {self.BEFORE_DATE} is setting ---")
        self.GOOGLE_TIMEMIN = (date.today(
        ) + timedelta(days=- data["goback_days"])).strftime(f"%Y-%m-%dT%H:%M:%S{self.TIMECODE}")
        print(f"--- google_timemin: {self.GOOGLE_TIMEMIN} is setting ---")
        self.GOOGLE_TIMEMAX = (date.today(
        ) + timedelta(days=+ data["goforward_days"])).strftime(f"%Y-%m-%dT%H:%M:%S{self.TIMECODE}")
        print(f"--- google_timemax: {self.GOOGLE_TIMEMAX} is setting ---")
        self.DELETE_OPTION = data["delete_option"]
        print(f"--- delete_option: {self.DELETE_OPTION} is setting ---")
        self.DEFAULT_EVENT_LENGTH = data["default_event_length"]
        print(f"--- default_event_length: {self.DEFAULT_EVENT_LENGTH} is setting ---")
        # 8 would be 8 am. 16 would be 4 pm. Only int
        self.DEFAULT_EVENT_START = data["default_start_time"]
        print(f"--- default_start_time: {self.DEFAULT_EVENT_START} is setting ---")
        # 0 Notion -> GCal: be created as an all-day event
        # 1 Notion -> GCal: be created at whatever hour you defined in the DEFAULT_EVENT_START
        self.ALLDAY_OPTION = data["allday_option"]
        print(f"--- allday_option: {self.ALLDAY_OPTION} is setting ---")
        # MULTIPLE CALENDAR PART:
        self.GCAL_DIC = data["gcal_dic"][0]
        print(f"--- gcal_dic: {self.GCAL_DIC} is setting ---")
        self.GCAL_DIC_KEY_TO_VALUE = self.gcal_dic_key_to_value(
            data["gcal_dic"][0])
        print(f"--- gcal_dic_key_to_value: {self.GCAL_DIC_KEY_TO_VALUE} is setting ---")
        # Default calendar Setting
        self.GCAL_DEFAULT_NAME = list(self.GCAL_DIC)[0]
        print(f"--- gcal_default_name: {self.GCAL_DEFAULT_NAME} is setting ---")
        self.GCAL_DEFAULT_ID = list(self.GCAL_DIC_KEY_TO_VALUE)[0]
        print(f"--- gcal_default_id: {self.GCAL_DEFAULT_ID} is setting ---")
        # DATABASE SPECIFIC EDITS
        self.TASK_NOTION_NAME = data["page_property"][0]["Task_Notion_Name"]
        print(f"--- task_notion_name: {self.TASK_NOTION_NAME} is setting ---")
        self.DATE_NOTION_NAME = data["page_property"][0]["Date_Notion_Name"]
        print(f"--- date_notion_name: {self.DATE_NOTION_NAME} is setting ---")
        self.INITIATIVE_NOTION_NAME = data["page_property"][0]["Initiative_Notion_Name"]
        print(f"--- initiative_notion_name: {self.INITIATIVE_NOTION_NAME} is setting ---")
        self.EXTRAINFO_NOTION_NAME = data["page_property"][0]["ExtraInfo_Notion_Name"]
        print(f"--- extrainfo_notion_name: {self.EXTRAINFO_NOTION_NAME} is setting ---")
        self.LOCATION_NOTION_NAME = data["page_property"][0]["Location_Notion_Name"]
        print(f"--- location_notion_name: {self.LOCATION_NOTION_NAME} is setting ---")
        self.ON_GCAL_NOTION_NAME = data["page_property"][0]["On_GCal_Notion_Name"]
        print(f"--- on_gcal_notion_name: {self.ON_GCAL_NOTION_NAME} is setting ---")
        self.NEEDGCALUPDATE_NOTION_NAME = data["page_property"][0]["NeedGCalUpdate_Notion_Name"]
        print(f"--- needgcalupdate_notion_name: {self.NEEDGCALUPDATE_NOTION_NAME} is setting ---")
        self.GCALEVENTID_NOTION_NAME = data["page_property"][0]["GCalEventId_Notion_Name"]
        print(f"--- gcaleventid_notion_name: {self.GCALEVENTID_NOTION_NAME} is setting ---")
        self.LASTUPDATEDTIME_NOTION_NAME = data["page_property"][0]["LastUpdatedTime_Notion_Name"]
        print(f"--- lastupdatedtime_notion_name: {self.LASTUPDATEDTIME_NOTION_NAME} is setting ---")
        self.CALENDAR_NOTION_NAME = data["page_property"][0]["Calendar_Notion_Name"]
        print(f"--- calendar_notion_name: {self.CALENDAR_NOTION_NAME} is setting ---")
        self.CURRENT_CALENDAR_ID_NOTION_NAME = data["page_property"][0]["Current_Calendar_Id_Notion_Name"]
        print(f"--- current_calendar_id_notion_name: {self.CURRENT_CALENDAR_ID_NOTION_NAME} is setting ---")

        # set at 0 if you want the delete column
        # set at 1 if you want nothing deleted
        self.DELETE_NOTION_NAME = data["page_property"][0]["Delete_Notion_Name"]
        print(f"--- delete_notion_name: {self.DELETE_NOTION_NAME} is setting ---")
        self.STATUS_NOTION_NAME = data["page_property"][0]["Status_Notion_Name"]
        print(f"--- status_notion_name: {self.STATUS_NOTION_NAME} is setting ---")
        self.PAGE_ID_NOTION_NAME = data["page_property"][0]["Page_ID_Notion_Name"]
        print(f"--- page_id_notion_name: {self.PAGE_ID_NOTION_NAME} is setting ---")
        self.COMPLETEICON_NOTION_NAME = data["page_property"][0]["CompleteIcon_Notion_Name"]
        print(f"--- completeicon_notion_name: {self.COMPLETEICON_NOTION_NAME} is setting ---")
        self.SKIP_DESCRIPTION_CONDITION = data["skip_description_condition"]
        print(f"--- skip_description_condition: {self.SKIP_DESCRIPTION_CONDITION} is setting ---")
        # set notion auth
        self.NOTION = Client(auth=data["notion_token"])
        print("--- Init Toke.py Notion class ---")

    def gcal_dic_key_to_value(self, gcal_dic):
        key_to_value = {}
        for key in gcal_dic:
            key_to_value[gcal_dic[key]] = key
        return key_to_value

    def get_database_id(self, url):
        # Define the regular expression pattern
        pattern = r"https://www.notion.so/[^/]+/([^?]+)"

        # Search for the pattern in the URL
        match = re.search(pattern, url)
        if match:
            extracted_string = match.group(1)
            return extracted_string
        else:
            print("Error: No match database ID")
            sys.exit(1)

    def get_string(self):
        print("--- Token Notion Activated ---")

# google API setting


class Google():
    def __init__(self):
        if os.path.exists(CREDPATH):
            credentials = pickle.load(open(CREDPATH, "rb"))
            self.service = build("calendar", "v3", credentials=credentials)
        else:
            print("Make sure you store token.pkl in toke folder")
        try:
            if os.path.exists(FILEPATH):
                print("Notion setting file found")
                with open(FILEPATH) as f:
                    data = json.load(f)
                    self.DOCKER = data["docker"]
        except:
            print("Make sure you store notion_setting.json in toke folder")
            print("Or incrrect json format")
            os._exit(1)
        try:
            gcal_default_id = Notion().GCAL_DEFAULT_ID
            calendar = self.service.calendars().get(
                calendarId=gcal_default_id).execute()
            print(f"--- Init Toke.py Google class ---")
            print(f"--- {self.service} ---")
        except:
            # ready to refresh the token and close the program
            print(
                "Checking if the Google Calendar API token expires. \nRun Token.py to update the token.pkl.")
            print(
                "Google Cloud Platform https://console.cloud.google.com/apis/credentials")
            print("Make sure tha you have the right client_secret.json in token folder")
            self.ask_creds(CREDPATH)
            os._exit(1)

    # DO NOT SHARE WITH OTHERS

    def ask_creds(self, CREDPATH):
        # If modifying these scopes, delete the file `token.json`
        scopes = ["https://www.googleapis.com/auth/calendar"]
        creds = None
        # The file token.pkl stores the user"s access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(CREDPATH):
            try:
                creds = Credentials.from_authorized_user_file(
                    CREDPATH, scopes)
            except:
                os.remove(CREDPATH)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(CLIENTPATH, scopes)
                if self.DOCKER:
                    print("Run in docker container")
                    # Post the cred to terminal and copy the code to the terminal
                    creds = flow.run_console()
                else:
                    print("Run in local server")
                    # Easy: Use local server while not in docker container
                    creds = flow.run_local_server(port=0)
                print("------------------Refresh tokens------------------")
                print("\n")
            # Save the credentials for the next run
            with open(CREDPATH, "wb") as token:
                print("Save the credentials for the next run")
                pickle.dump(creds, token)

    def get_string(self):
        print("--- Token Google Activated ---")