#!/usr/bin/python3.6
# coding: utf8
import numpy as np
import pandas as pd
import datetime
import json
import os
import re

import sys #required because files in parent folder
sys.path.append('../')
import config

import sys #required because files in other folder
sys.path.append('../classes/')
from db_bot import DBBot

DBBot = DBBot()

class DialogueBot:
    def setup(self):
        # wipe existing dialogues first
        DBBot.wipe_dialogues()
        print('wiped dialogues')
        # load the dialogues into the db
        file_identifiers = os.listdir("{}/dialogues/".format(config.DIRECTORY))
        # remove hidden files
        file_identifiers = [i for i in file_identifiers if i.endswith('.csv')]
        # remove extension
        file_identifiers = [os.path.splitext(each)[0] for each in file_identifiers]
        DialogueBot.save_dialogues(file_identifiers)

    def save_dialogues(file_identifiers):
        print('saving dialogues')
        for identifier in file_identifiers:
            data = pd.read_csv("{}/dialogues/{}.csv".format(config.DIRECTORY, identifier), dtype= str, delimiter=',')
            # translate NaN cells into None cells
            data = data.where(pd.notnull(data), None)
            # transform keyboard list into actual list
            f = lambda x: x.split("; ") if x is not None else x
            data["keyboard"] = data["keyboard"].apply(f)
            # transform array into subscriptable numpy array
            data=np.array(data, dtype=object)
            #add slash to match the intent
            identifier = '/' + identifier
            DBBot.add_dialogue(identifier, json.dumps(data.tolist()))

    def fetch_dialogue(file_identifier):
        data = DBBot.get_dialogue(file_identifier)
        data = json.loads(data[0][2])
        data = np.array(data, dtype = object)
        # convert strings into list
        return data

    def fetch_last_messages(data, chat_id, last_user_message=None, last_bot_message=None):
        # if triggered, the last_user_message will be set to "✏"
        if last_user_message is None:
            # get last user message
            last_user_message = DBBot.get_last_message(chat_id, 0)[1]
        # check if user provided open answer - if so, change message to "✏". If user sent photo, start meal_entry
        if len(data[data[:, 1]==last_user_message, 0]) == 0:
            if np.char.startswith(data[:, 1][0], "/meal_entry") and "photo" in last_user_message:
                last_user_message = data[:, 1][0]
            else:
                last_user_message = "✏"

        # if triggered, the last_bot_message will be set to "✏"
        if last_bot_message is None:
            # get last bot message; if there is no previous bot message, set "✏"
            result_last_bot_message = DBBot.get_last_message(chat_id, 1)
            if result_last_bot_message == None:
                last_bot_message = "✏"
            else:
                last_bot_message = result_last_bot_message[1]

        # check if bot response is in array; if not, change message to "✏"
        last_bot_message_for_exception = None
        if len(data[data[:, 0]==last_bot_message, 0]) == 0:
            # this value is used for the except: statement
            last_bot_message_for_exception = last_bot_message
            last_bot_message = "✏"
        return last_user_message, last_bot_message, last_bot_message_for_exception

    def extract_response_array(response_array, chat_id):
        # save parameters
        message = response_array[2]
        keyboard = response_array[3]
        photo = response_array[6]
        key_value = response_array[7]
        intent = response_array[8]
        # check for key_values (chat_id, datetime)
        if '{}' in message:
            # check if a value in the message has to be retrieved from db
            if 'dbvalue' in message:
                # get last value from db
                retrieve_from_db = re.findall(r'\bdbvalue\w+', message)[0].split("_",1)[1]
                data = DBBot.get_key_values(key_value = retrieve_from_db, telegram_id = chat_id)
                # define variable name
                vars()[re.findall(r'\bdbvalue\w+', message)[0]] = data[0][4]

            # convert string to message with .format
            message = eval(message)
        if photo and '{}' in photo:
            photo = eval(photo)
        return message, keyboard, photo, key_value, intent

    def find_response(self, intent, chat_id, last_user_message=None, last_bot_message=None):
        # get the dialogue
        try:
            data = DialogueBot.fetch_dialogue(intent)
        except Exception as e:
            print(e)
            intent = '/wrong_command'
            last_user_message = '/wrong_command'
            data = DialogueBot.fetch_dialogue(intent)

        last_user_message, last_bot_message, last_bot_message_for_exception = DialogueBot.fetch_last_messages(data, chat_id, last_user_message, last_bot_message)

        try:
            response_array = data[(intent == last_user_message == data[:,1]) | ((last_bot_message == data[:,0]) & (last_user_message == data[:,1]))][0]
        except:
            # check if {} formating values have been used - necessary for processing the user message
            temp = data[np.array(["{}" in s for s in data[:,0]])]
            for num, row in enumerate(temp):
                # check if a value in the message has to be retrieved from db
                if 'dbvalue' in temp[num, 0]:
                    # get last value from db
                    retrieve_from_db = re.findall(r'\bdbvalue\w+', temp[num, 0])[0].split("_",1)[1]
                    data = DBBot.get_key_values(key_value = retrieve_from_db, telegram_id = chat_id)
                    # check if any values so far
                    if data:
                        # define variable name
                        vars()[re.findall(r'\bdbvalue\w+', temp[num, 0])[0]] = data[0][4]
                    else:
                        vars()[re.findall(r'\bdbvalue\w+', temp[num, 0])[0]] = '-'
                if last_user_message == temp[num, 1] and last_bot_message_for_exception == eval(temp[num, 0]):
                    response_array = temp[num, :]
        # check if response_array exists. If not, set default answer <- catch-all for errors in dialogues
        if 'response_array' not in locals():
            try:
                # check if the user double clicked a button by replacing the user message with "✏".
                response_array = data[(intent == "✏" == data[:,1]) | ((last_bot_message == data[:,0]) & ("✏" == data[:,1]))][0]
            except Exception as e:
                print(e)
                response_array = ['✏', '✏', 'Tut mir leid. Das verstehe ich nicht 😔. Ich habe meine Macher schon verständigt.', None, None, None, None, None, '/open_conversation']

        message, keyboard, photo, key_value, intent = DialogueBot.extract_response_array(response_array, chat_id)

        return message, keyboard, photo, key_value, intent
