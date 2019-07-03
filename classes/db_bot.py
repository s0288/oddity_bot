#!/usr/bin/python3.6
# coding: utf8

from time import sleep
from sqlalchemy import *

import sys #required because files in other folder
sys.path.append('../')
import config


class DBBot:
    def __init__(self):
        engine = create_engine(config.POSTGRES)
        metadata = MetaData(engine)
        self.conn = engine.connect()

    def setup(self):
        print("creating non-existent tables")
        updates_stmt = 'CREATE TABLE IF NOT EXISTS updates (id serial primary key, message_id int, created_at timestamp, received_at timestamp, message text, intent text, telegram_id int, chat_id int, chat_type text, bot_command text, key_value text, is_bot boolean, callback_query_id bigint, group_chat_created int, new_chat_participant_id int, update_id int, time_to_send float)'
        users_stmt = 'CREATE TABLE IF NOT EXISTS users (id serial primary key, telegram_id int, first_name text, created_at timestamp, received_at timestamp, is_bot boolean, language_code text, is_user boolean)'
        user_menus_stmt = 'CREATE TABLE IF NOT EXISTS user_menus (id serial primary key, telegram_id int, chat_id int, category text, value text, created_at timestamp)'
        dialogues_stmt = 'CREATE TABLE IF NOT EXISTS dialogues (id serial primary key, intent text, np_array text)'
        key_values_stmt = 'CREATE TABLE IF NOT EXISTS key_values (id serial primary key, telegram_id int, chat_id int, key_value text, value text, created_at timestamp, received_at timestamp)'
        files_stmt = 'CREATE TABLE IF NOT EXISTS files (id serial primary key, telegram_id int, chat_id int, intent text, key_value text, file text, created_at timestamp, received_at timestamp)'
        triggers_stmt = 'CREATE TABLE IF NOT EXISTS triggers (id serial primary key, telegram_id int, chat_id int, trigger_value text, trigger_time text, trigger_day text, created_at timestamp, received_at timestamp)'
        typeform_stmt = 'CREATE TABLE IF NOT EXISTS typeform_responses (id serial primary key, custom_id int, landing_id text, response_id text, landed_at timestamp, submitted_at timestamp, received_at timestamp, field_id text, field_type text, answer_type text, answer_value text)'
        updateididx = 'CREATE INDEX IF NOT EXISTS idIndex ON updates (id ASC)'
        userididx = 'CREATE INDEX IF NOT EXISTS idUserIndex ON users (id ASC)'
        self.conn.execute(updates_stmt)
        self.conn.execute(users_stmt)
        self.conn.execute(user_menus_stmt)
        self.conn.execute(dialogues_stmt)
        self.conn.execute(key_values_stmt)
        self.conn.execute(files_stmt)
        self.conn.execute(triggers_stmt)
        self.conn.execute(typeform_stmt)
        self.conn.execute(updateididx)
        self.conn.execute(userididx)

# bot_main functions
    def get_active_users(self, telegram_ids_only=None):
        if telegram_ids_only is None:
            stmt = "SELECT id, telegram_id, first_name, created_at, received_at, is_bot, language_code, is_user FROM users WHERE is_user is TRUE AND is_bot is False"
        else:
            stmt = "SELECT telegram_id FROM users WHERE is_user is TRUE AND is_bot is False"
        try:
            return self.conn.execute(stmt).fetchall()
        except Exception as e:
            print(e)

    def get_trigger_values(self, telegram_id=None, trigger_value=None):
        if telegram_id == None and trigger_value == None:
            stmt = 'SELECT telegram_id, chat_id, trigger_value, trigger_time, trigger_day, created_at FROM triggers ORDER BY id DESC'
            args = []
        elif trigger_value is not None:
            stmt = 'SELECT telegram_id, chat_id, trigger_value, trigger_time, trigger_day, created_at FROM triggers WHERE trigger_value = %s ORDER BY id DESC'
            args = [trigger_value]
        else:
            stmt = 'SELECT telegram_id, chat_id, trigger_value, trigger_time, trigger_day, created_at FROM triggers WHERE telegram_id in {} ORDER BY id DESC'.format(telegram_id)
            args = []
        try:
            return self.conn.execute(stmt, args).fetchall()
        except Exception as e:
            print('in exception')
            print(e)

# update functions
    def add_message(self, message_id, created_at, received_at, message, intent, telegram_id, chat_id, chat_type, bot_command, key_value, is_bot, callback_query_id, group_chat_created, new_chat_participant_id, update_id):
        stmt = 'INSERT INTO updates (message_id, created_at, received_at, message, intent, telegram_id, chat_id, chat_type, bot_command, key_value, is_bot, callback_query_id, group_chat_created, new_chat_participant_id, update_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
        args = [message_id, created_at, received_at, message, intent, telegram_id, chat_id, chat_type, bot_command, key_value, is_bot, callback_query_id, group_chat_created, new_chat_participant_id, update_id]
        try:
            self.conn.execute(stmt, args)
        except Exception as e:
            print(e)

    def get_last_message(self, chat_id, is_bot):
        stmt = 'SELECT intent, message, key_value FROM updates WHERE chat_id = %s AND is_bot = cast(%s as boolean) ORDER BY id DESC LIMIT 1'
        args = [chat_id, is_bot]
        result = self.conn.execute(stmt, args).fetchall()
        # if there are no bot messages yet, return None
        if result:
            return result[0]
        else:
            return None

## update functions - user functions
    def add_user(self, telegram_id, first_name, created_at, received_at, is_bot, language_code):
        stmt = 'INSERT INTO users (telegram_id, first_name, created_at, received_at, is_bot, language_code, is_user) VALUES (%s, %s, %s, %s, %s, %s, True)'
        args = [telegram_id, first_name, created_at, received_at, is_bot, language_code]
        self.conn.execute(stmt, args)

    def check_user(self, telegram_id):
        stmt = 'SELECT COUNT(*) FROM users WHERE telegram_id = %s'
        args = [telegram_id]
        return self.conn.execute(stmt, args).fetchall()[0][0]

## update functions - user menu functions
    def get_user_menu(self, menu_type, chat_id):
        if menu_type == 'main':
            stmt = "SELECT category FROM user_menus WHERE chat_id = %s GROUP BY category"
            args = [chat_id]
        else:
            stmt = "SELECT value FROM user_menus WHERE (category = %s OR category = 'zurueck') AND chat_id = %s GROUP BY value"
            args = [menu_type, chat_id]
        try:
            return self.conn.execute(stmt, args).fetchall()
        except Exception as e:
            print(e)

    def check_profile(self, telegram_id, chat_id, category, profile_value):
        stmt = 'SELECT COUNT(*) FROM user_menus WHERE telegram_id = %s AND chat_id = %s AND category = %s AND value = %s'
        args = [telegram_id, chat_id, category, profile_value]
        return self.conn.execute(stmt, args).fetchall()[0][0]

    def add_to_profile(self, telegram_id, chat_id, category, profile_value, created_at):
        stmt = 'INSERT INTO user_menus (telegram_id, chat_id, category, value, created_at) VALUES (%s, %s, %s, %s, %s)'
        args = [telegram_id, chat_id, category, profile_value, created_at]
        self.conn.execute(stmt, args)


# dialogue functions
    def wipe_dialogues(self):
        stmt = "DELETE FROM dialogues"
        # if there are no matches, return None
        result = self.conn.execute(stmt)

    def add_dialogue(self, intent, np_array):
        stmt = 'INSERT INTO dialogues (intent, np_array) VALUES (%s, %s)'
        args = [intent, np_array]
        try:
            self.conn.execute(stmt, args)
        except Exception as e:
            print(e)

    def get_dialogue(self, intent_identifier):
        stmt = "SELECT * FROM dialogues WHERE intent = %s ORDER BY id DESC"
        args = [intent_identifier]
        # if there are no matches, return None
        result = self.conn.execute(stmt, args).fetchall()
        if result:
            return self.conn.execute(stmt, args).fetchall()
        else:
            return None

# data functions
    def get_last_value(self, context):
        if context == 'files':
            stmt = "SELECT MAX(created_at) FROM files"
            args = []
        elif context == 'key_values':
            stmt = "SELECT MAX(created_at) FROM key_values"
            args = []
        elif context == 'typeform':
            stmt = "SELECT max(submitted_at) FROM typeform_responses"
            args = []
        try:
            return self.conn.execute(stmt, args).fetchall()[0]
        except Exception as e:
            print(e)

    def get_values_from_updates(self, context, last_value=None):
        if context == 'files':
            if last_value is None:
                stmt = "SELECT telegram_id, chat_id, message, key_value, intent, created_at FROM updates WHERE message like 'photo: %%' ORDER BY id DESC"
                args = []
            else:
                stmt = "SELECT telegram_id, chat_id, message, key_value, intent, created_at FROM updates WHERE message like 'photo: %%' AND created_at > %s ORDER BY id DESC"
                args = [last_value]
        else:
            if last_value is None:
                stmt = 'SELECT telegram_id, chat_id, message, key_value, intent, created_at, is_bot FROM updates WHERE key_value is not Null AND is_bot = cast(0 as boolean) ORDER BY id DESC'
                args = []
            else:
                stmt = 'SELECT telegram_id, chat_id, message, key_value, intent, created_at, is_bot FROM updates WHERE key_value is not Null AND is_bot = cast(0 as boolean) AND created_at > %s ORDER BY id DESC'
                args = [last_value]
        try:
            return self.conn.execute(stmt, args).fetchall()
        except Exception as e:
            print(e)

    ## key value retrieval
    def add_key_value(self, telegram_id, chat_id, key_value, value, created_at, received_at):
        stmt = 'INSERT INTO key_values (telegram_id, chat_id, key_value, value, created_at, received_at) VALUES (%s, %s, %s, %s, %s, %s)'
        args = [telegram_id, chat_id, key_value, value, created_at, received_at]
        self.conn.execute(stmt, args)

    def get_key_values(self, key_value=None, telegram_id=None):
        if key_value is None and telegram_id is None:
            stmt = 'SELECT key_values.id, key_values.telegram_id, key_values.chat_id, key_values.key_value, key_values.value, key_values.created_at, key_values.received_at FROM key_values join users on key_values.telegram_id = users.telegram_id WHERE users.is_user is True ORDER BY key_values.created_at DESC'
            args = []
        elif key_value is not None and telegram_id is None:
            stmt = 'SELECT key_values.id, key_values.telegram_id, key_values.chat_id, key_values.key_value, key_values.value, key_values.created_at, key_values.received_at FROM key_values join users on key_values.telegram_id = users.telegram_id WHERE key_values.key_value = %s AND users.is_user is True ORDER BY key_values.created_at DESC'
            args = [key_value]
        elif key_value is not None and telegram_id is not None:
            stmt = 'SELECT key_values.id, key_values.telegram_id, key_values.chat_id, key_values.key_value, key_values.value, key_values.created_at, key_values.received_at FROM key_values join users on key_values.telegram_id = users.telegram_id WHERE key_values.key_value = %s AND key_values.telegram_id = %s AND users.is_user is True ORDER BY key_values.created_at DESC'
            args = [key_value, telegram_id]
        try:
            return self.conn.execute(stmt, args).fetchall()
        except Exception as e:
            print(e)

    ## file retrieval
    def add_file(self, telegram_id, chat_id, intent, key_value, file, created_at, received_at):
        stmt = 'INSERT INTO files (telegram_id, chat_id, intent, key_value, file, created_at, received_at) VALUES (%s, %s, %s, %s, %s, %s, %s)'
        args = [telegram_id, chat_id, intent, key_value, file, created_at, received_at]
        try:
            self.conn.execute(stmt, args)
        except Exception as e:
            print(e)

    ## trigger functions
    def check_triggers(self, telegram_id, chat_id, trigger_value, trigger_day, trigger_time):
        stmt = 'SELECT COUNT(*) FROM triggers WHERE telegram_id = %s AND chat_id = %s AND trigger_value = %s AND trigger_day = %s AND trigger_time = %s'
        args = [telegram_id, chat_id, trigger_value, trigger_day, trigger_time]
        return self.conn.execute(stmt, args).fetchall()[0][0]

    def add_trigger(self, telegram_id, chat_id, trigger_value, trigger_time, trigger_day, created_at, received_at):
        stmt = 'INSERT INTO triggers (telegram_id, chat_id, trigger_value, trigger_time, trigger_day, created_at, received_at) VALUES (%s, %s, %s, %s, %s, %s, %s)'
        args = [telegram_id, chat_id, trigger_value, trigger_time, trigger_day, created_at, received_at]
        self.conn.execute(stmt, args)

    def delete_triggers_by_inactive_users(self):
        stmt = 'DELETE FROM triggers USING users WHERE triggers.telegram_id = users.telegram_id AND users.is_user = False'
        args = []
        try:
            self.conn.execute(stmt, args)
        except Exception as e:
            print(e)

    def delete_from_triggers(self, telegram_id, trigger_value, trigger_day, created_at):
        stmt = 'DELETE FROM triggers WHERE telegram_id = %s AND trigger_value = %s AND trigger_day = %s AND created_at = %s'
        args = [telegram_id, trigger_value, trigger_day, created_at]
        try:
            self.conn.execute(stmt, args)
        except Exception as e:
            print(e)


####### remove later
    def add_typeform_response(self, custom_id, landing_id, response_id, landed_at, submitted_at, received_at, field_id, field_type, answer_type, answer_value):
        stmt = 'INSERT INTO typeform_responses (custom_id, landing_id, response_id, landed_at, submitted_at, received_at, field_id, field_type, answer_type, answer_value) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
        args = [custom_id, landing_id, response_id, landed_at, submitted_at, received_at, field_id, field_type, answer_type, answer_value]
        try:
            self.conn.execute(stmt, args)
        except Exception as e:
            print(e)

    def check_typeform(self, landing_id, field_id):
        stmt = 'SELECT COUNT(*) FROM typeform_responses WHERE landing_id = %s AND field_id = %s'
        args = [landing_id, field_id]
        return self.conn.execute(stmt, args).fetchall()[0][0]
