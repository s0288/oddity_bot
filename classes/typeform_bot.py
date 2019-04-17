import requests
import json
import datetime

import sys #required because files in parent folder
sys.path.append('../')
import config

import sys #required because files in other folder
sys.path.append('../classes/')
from db_bot import DBBot

DBBot = DBBot()
TYPEFORM_AUTHORIZATION = config.TYPEFORM_AUTHORIZATION

last_value = DBBot.get_last_value('typeform')
last_value = last_value[0].date().strftime('%Y-%m-%d')

headers = {'Authorization': 'Bearer ' + TYPEFORM_AUTHORIZATION, 'Accept': 'application/json'}
r = requests.get("https://api.typeform.com/forms/ASHAdA/responses?since={}T00%3A00%3A00&page_size=999".format(last_value), headers=headers)
r.encoding = 'utf-8'
json_data = json.loads(r.text)

try:
    for i in range(0,len(json_data['items'])):
        custom_id = json_data['items'][i]["hidden"]["id"]
        landing_id = json_data['items'][i]["landing_id"]
        response_id = json_data['items'][i]["response_id"]
        landed_at = json_data['items'][i]["landed_at"]
        submitted_at = json_data['items'][i]["submitted_at"]
        if json_data['items'][i].get("answers") != None:
            for j in range(0,len(json_data['items'][i]["answers"])):
                field_id = json_data['items'][i]["answers"][j]["field"]["id"]
                field_type = json_data['items'][i]["answers"][j]["field"]["type"]
                answer_type = json_data['items'][i]["answers"][j]["type"]
                if answer_type == 'number':
                    answer_value = json_data['items'][i]["answers"][j]["number"]
                elif answer_type == 'choice':
                    answer_value = json_data['items'][i]["answers"][j]["choice"]["label"]
                elif answer_type == 'text':
                    answer_value = json_data['items'][i]["answers"][j]["text"]
                elif answer_type == 'text':
                    answer_value = json_data['items'][i]["answers"][j]["text"]
                if DBBot.check_typeform(landing_id, field_id) == 0:
                    received_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    # add user_id, first_name, created_at, is_bot, language_code
                    DBBot.add_typeform_response(custom_id, landing_id, response_id, landed_at, submitted_at, received_at, field_id, field_type, answer_type, answer_value)
                    print("Added: Typeform response")
                else:
                    print("Typeform response already there")
except Exception as e:
    print(e)
