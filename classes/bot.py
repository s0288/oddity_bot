#!/usr/bin/python3.6
# coding: utf8
import requests
import json
import datetime
import urllib
import os

import sys #required because files in other folder
sys.path.append('../classes/')
from db_bot import DBBot
from dialogue_bot import DialogueBot

import sys #required because files in parent folder
sys.path.append('../')
import config

TOKEN = config.TELEGRAM_TOKEN
URL = "https://api.telegram.org/bot{}/".format(TOKEN)
DBBot = DBBot()
DialogueBot = DialogueBot()

class Bot:

# ------ process incoming messages
    def get_json_from_url(url):
        response = requests.get(url)
        content = response.content.decode("utf8")
        js = json.loads(content)
        return js

    def get_updates(self, offset=None):
        url = URL + "getUpdates?timeout=600"
        if offset:
            url += "&offset={}".format(offset)
        js = Bot.get_json_from_url(url)
        return js

    def get_last_update_id(self, updates):
        update_ids = []
        for update in updates["result"]:
            update_ids.append(int(update["update_id"]))
        return min(update_ids)
# ------ end: process incoming messages

# ------ extract content of incoming messages
    # key function to save to database
    def save_messages(message_elements):
        # set time when message was saved to db
        message_elements['received_at'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # check if user is in db already; if not, add him
        ## possible improvement: add a global variable later to avoid checking the db at every message
        if message_elements['is_bot'] is not None:
            if DBBot.check_user(message_elements['user_id']) == 0:
                # add user_id, first_name, created_at, is_bot, language_code
                DBBot.add_user(message_elements['user_id'], message_elements['first_name'], message_elements['created_at'], message_elements['received_at'], message_elements['is_bot'], message_elements['language_code'])

        # save message to db
        try:
            DBBot.add_message(message_elements['message_id'], message_elements['created_at'], message_elements['received_at'], message_elements['message'], message_elements['intent'], message_elements['user_id'], message_elements['chat_id'], message_elements['chat_type'], message_elements['bot_command'], message_elements['key_value'], message_elements['is_bot'], message_elements['callback_query_id'], message_elements['group_chat_created'], message_elements['new_chat_participant_id'], message_elements['update_id'])
        except Exception as e:
            print(e)

    # invoked in extract_updates()
    def check_content(update):
        content = None
        # check whether we're dealing with a message or a callback
        if update.get('message') is not None:
            if update["message"].get('group_chat_created') is None or update["message"].get('new_chat_participant') is None or update["message"].get('left_chat_participant') is None:
                content = 'extract_message'
            else:
                print('do_not_extract_event')
                content = 'do_not_extract'
        elif update.get('callback_query') is not None:
            content = 'extract_callback'
        return content

    # invoked in extract_updates()
    def extract_message(message_elements, message):
        # save attributes
        message_elements['created_at'] = datetime.datetime.fromtimestamp(int(message["date"])).strftime('%Y-%m-%d %H:%M:%S')
        message_elements['message_id'] = message["message_id"]
        # if the message has text, save it
        if message.get('text') is not None:
            message_elements['message'] = message["text"]
        elif message.get('document') is not None and message["from"]["is_bot"] is False:
            message_elements['message'] = 'photo: ' + message["document"]["file_id"]
        # check if user sent a meal picture (but make sure that bot photos are sent through!)
        elif message.get('photo') is not None and message["from"]["is_bot"] is False:
            try:
                message_elements['message'] = 'photo: ' + message["photo"][3]["file_id"]
                message_elements['key_value'] = 'user_photo'
            except:
                message_elements['message'] = 'photo: ' + message["photo"][0]["file_id"]
                message_elements['key_value'] = 'user_photo'
        message_elements['user_id'] = message["from"]["id"]
        message_elements['first_name'] = message["from"]["first_name"]
        message_elements['chat_id'] = message["chat"]["id"]
        message_elements['chat_type'] = message["chat"]["type"]
        # if the user sends a bot_command (e.g. /start or /check_in), save it
        if message.get('entities') is not None:
            for entity in message["entities"]:
                message_elements['bot_command'] = entity["type"]
        message_elements['is_bot'] = message["from"]["is_bot"]
        # if the message has a language code, save it
        if message["from"].get('language_code') is not None:
            message_elements['language_code'] = message["from"]["language_code"]
        return message_elements

    def get_intent(message_elements):
        # set bot_command as intent
        if message_elements["bot_command"] == 'bot_command':
            message_elements["intent"] = message_elements["message"].lower()
        # if there is no bot command, continue the discussion that is under way or set 'open_conversation'
        else:
            # get the intent and the key value of the last bot message
            last_bot_message = DBBot.get_last_message(message_elements["chat_id"], 1)
            # it is possible that there are no bot messages yet, therefore check if None
            if last_bot_message:
                last_intent, last_msg, last_key_value = last_bot_message[0], last_bot_message[1], last_bot_message[2]
                if message_elements['key_value'] in ('user_photo', 'meal_entry'):
                    message_elements["intent"] = '/meal_entry'
                elif last_intent == 'end_conversation' or last_intent is None:
                    message_elements["intent"] = 'open_conversation'
                else:
                    message_elements["intent"] = last_intent
                    if message_elements["key_value"] != 'user_photo':
                        message_elements["key_value"] = last_key_value
            else:
                message_elements["intent"] = 'open_conversation'
        return message_elements

    # main extract_ function that defines where an update is routed towards
    def extract_updates(self, updates):
        for update in updates["result"]:
            # message container for incoming and outgoing msgs
            message_elements = {'update_id': None, 'created_at': None, 'received_at': None, 'message_id': None, 'message': None, 'intent': None, 'keyboard': None, 'user_id': None, 'first_name': None, 'chat_id': None, 'chat_title': None, 'chat_type': None, 'bot_command': None, 'key_value': None, 'photo': None, 'is_bot': None, 'language_code': None, 'callback_query_id': None, 'group_chat_created': None, 'new_chat_participant_id': None}

            # check whether we're dealing with a message, a callback or not-to-be-extracted content
            content = Bot.check_content(update)
            if content not in ['do_not_extract', 'extract_callback']:
                if content == 'extract_message':
                    message_elements = Bot.extract_message(message_elements, update['message'])
                message_elements = Bot.get_intent(message_elements)
                Bot.save_messages(message_elements)
                return message_elements
# ------ end: extract content of incoming messages

# ------ start: send messages
    def send_message(message_elements):
        parsed_message = urllib.parse.quote_plus(message_elements["message"])
        url = URL + "sendMessage?text={}&chat_id={}&parse_mode=HTML&disable_web_page_preview=true".format(parsed_message, message_elements["chat_id"])
        # remove keyboard from the background if no new keyboard is provided
        if message_elements["keyboard"]:
            url += "&reply_markup={}".format(message_elements["keyboard"])
        else:
            url += "&reply_markup={\"remove_keyboard\":%20true}"
        # send message and save response
        url_response = Bot.get_json_from_url(url)
        print(url_response)
        message_elements = Bot.extract_message(message_elements, url_response["result"])
        Bot.save_messages(message_elements)

    def send_photo(message_elements):
        #photo, chat_id, caption=None, reply_markup=None
        url = URL + "sendPhoto?photo={}&chat_id={}&parse_mode=HTML".format(message_elements["photo"], message_elements["chat_id"])
        if message_elements["message"]:
            url += "&caption={}".format(message_elements["message"])
        if message_elements["keyboard"]:
            url += "&reply_markup={}".format(message_elements["keyboard"])
        else:
            url += "&reply_markup={\"remove_keyboard\":%20true}"
        url_response = Bot.get_json_from_url(url)
        message_elements = Bot.extract_message(message_elements, url_response["result"])
        Bot.save_messages(message_elements)

    # for gifs and pdfs
    def send_document(message_elements):
        #photo, chat_id, caption=None, reply_markup=None
        url = URL + "sendDocument?document={}&chat_id={}&parse_mode=HTML".format(message_elements["photo"], message_elements["chat_id"])
        if message_elements["message"]:
            url += "&caption={}".format(message_elements["message"])
        if message_elements["keyboard"]:
            url += "&reply_markup={}".format(message_elements["keyboard"])
        else:
            url += "&reply_markup={\"remove_keyboard\":%20true}"
        url_response = Bot.get_json_from_url(url)
        message_elements = Bot.extract_message(message_elements, url_response["result"])
        Bot.save_messages(message_elements)
# ------ end: send messages


# ------ handle updates
    def handle_updates(self, first_name, chat_id, intent, message):
        try:
            # message container for incoming and outgoing msgs
            message_elements = {'update_id': None, 'created_at': None, 'received_at': None, 'message_id': None, 'message': None, 'intent': None, 'keyboard': None, 'user_id': None, 'first_name': None, 'chat_id': None, 'chat_title': None, 'chat_type': None, 'bot_command': None, 'key_value': None, 'photo': None, 'is_bot': None, 'language_code': None, 'callback_query_id': None, 'group_chat_created': None, 'new_chat_participant_id': None}

            message_elements["intent"] = intent
            message_elements["chat_id"] = chat_id
            ##### TO DO: catch-all until fixed:
            if intent in ['open_conversation', 'end_conversation']:
                return
            ##### end catch-all
            elif intent == '/profil':
                message_elements["message"], message_elements["intent"], message_elements["keyboard"] = Bot.build_menu(message, intent, chat_id)
            else:
                message_elements["message"], message_elements["keyboard"], message_elements["photo"], message_elements["key_value"], message_elements["intent"] = DialogueBot.find_response(intent, chat_id)
                if message_elements["keyboard"]:
                    message_elements["keyboard"] = Bot.build_keyboard(message_elements["keyboard"])
                if message_elements["key_value"] and "p_" in message_elements["key_value"]:
                    Bot.add_to_profile(chat_id, "/"+message_elements["key_value"].split("_",1)[1])

            # check for photo, doc or other
            if message_elements["photo"]:
                file_type = os.path.splitext(message_elements["photo"])[1]
                if file_type == ".gif" or file_type == ".pdf":
                    Bot.send_document(message_elements)
                else:
                    Bot.send_photo(message_elements)
            else:
                Bot.send_message(message_elements)
        except Exception as e:
            print(e)


    def build_keyboard(items, inline_keyboard=None):
        keyboard = [[item] for item in items]
        reply_markup = {"keyboard": keyboard, "one_time_keyboard": True, "resize_keyboard": True}
        return json.dumps(reply_markup)
# ------ end: handle updates

# ------ start: profile functions
    def build_menu(message, intent, chat_id):
        keyboard = []
        # find info to display
        if message in ['/profil', '/Profil']:
            message = 'Hier kannst du Daten angeben.'
            data = DBBot.get_user_menu('main', chat_id)
        elif message == 'Weitere Daten':
            intent = '/data'
            message = 'Welche Daten möchtest du angeben?'
            data = DBBot.get_user_menu('data', chat_id)
        for row in data:
            keyboard.append(row[0])
        keyboard = Bot.build_keyboard(keyboard)
        return message, intent, keyboard


    def add_to_profile(chat_id, profile_value):
        if profile_value in ('/zurueck', '/mahlzeit', '/ketonwert', '/gewicht', '/fasten'):
            category = profile_value
        else:
            category = 'data'
        created_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if DBBot.check_profile(chat_id, chat_id, category, profile_value) == 0:
            DBBot.add_to_profile(chat_id, chat_id, category, profile_value, created_at)

# ------ start: trigger messages
    def trigger_message(self, intent, chat_id):
        message_elements = {'update_id': None, 'created_at': None, 'received_at': None, 'message_id': None, 'message': None, 'intent': None, 'keyboard': None, 'user_id': None, 'first_name': None, 'chat_id': None, 'chat_title': None, 'chat_type': None, 'bot_command': None, 'key_value': None, 'photo': None, 'is_bot': None, 'language_code': None, 'callback_query_id': None, 'group_chat_created': None, 'new_chat_participant_id': None}
        message_elements["chat_id"] = chat_id
        message_elements["message"], message_elements["keyboard"], message_elements["photo"], message_elements["key_value"], message_elements["intent"] = DialogueBot.find_response(intent, chat_id, last_user_message=intent, last_bot_message="✏")
        # if keyboard needed, get it
        if message_elements["keyboard"]:
            message_elements["keyboard"] = Bot.build_keyboard(message_elements["keyboard"])
        Bot.send_message(message_elements)
