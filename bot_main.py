#!/usr/bin/python3.6
# coding: utf8
import time

# used for cronjobs
import pandas as pd
import logging
from apscheduler.schedulers.background import BackgroundScheduler

import sys #required because files in other folder
sys.path.append('./classes/')
from bot import Bot
from db_bot import DBBot
from dialogue_bot import DialogueBot

Bot = Bot()
DBBot = DBBot()
DialogueBot = DialogueBot()


# called by scheduler.add_job in main()
# it will be executed in a thread by the scheduler
def trigger(intent, chat_id):
    print("starting {} ...".format(intent))
    Bot.trigger_message(intent, chat_id)


# used to discern trigger_time of job ("minutes" or "repeating")
def get_job_details(trigger_value):
    user_id = trigger_value[0]
    intent = trigger_value[2]
    trigger_time = trigger_value[3]
    trigger_day = trigger_value[4]

    # for some exercises we send hourly messages. Let's account for this here
    if "-" not in trigger_time:
        hour, minute = pd.to_datetime(trigger_time).hour, pd.to_datetime(trigger_time).minute
    else:
        hour = trigger_time
        minute = None
    return user_id, intent, trigger_time, trigger_day, hour, minute



def main(chat_id=None):
    ## main job
    # create non-existent tables
    DBBot.setup()
    # load the dialogues
    DialogueBot.setup()
    last_update_id = None

    # create scheduler
    scheduler = BackgroundScheduler()
    # set up logging
    logging.basicConfig()
    logging.getLogger('apscheduler').setLevel(logging.DEBUG)
    scheduler.start()
    # cache needed to make sure the same job isn't set up over and over again
    cache = []
    counter = 0

    while True:
        print('in while loop')
        try:
            ##### triggers
            #### get list of active user ids first, then create triggers for these
            #### IMPORTANT: Already-set-up triggers are not removed - currently needs to restart whenever a user is removed
            active_users = DBBot.get_active_users("telegram_ids_only")

            # add if stmt in case that no existing users yet
            if active_users:
                active_users = [x[0] for x in active_users]
                # security check (if there is only one user, duplicate entry)
                if len(active_users) == 1:
                    active_users = [active_users[0], active_users[0]]

                trigger_values = DBBot.get_trigger_values(telegram_id=tuple(active_users))
                for trigger_value in trigger_values:
                    if trigger_value not in cache:
                        try:
                            user_id, intent, trigger_time, trigger_day, hour, minute = get_job_details(trigger_value)
                            job = scheduler.add_job(trigger, trigger='cron', day_of_week=trigger_day, hour=hour, minute=minute, args=[intent, user_id], misfire_grace_time=10, name="{}:{}_{}".format(counter, user_id, intent), max_instances=999, id=str(counter))

                        except Exception as e:
                            print(e)
                            # continue to prevent incrementing cache & counter
                            continue
                        # add new jobs to cache to make sure they are only triggered once
                        cache.append(trigger_value)
                        counter += 1

            ##### listen for new messages
            updates = Bot.get_updates(last_update_id)
            ## main job
            if len(updates["result"]) > 0:
                last_update_id = Bot.get_last_update_id(updates) + 1
                # update_elements holds the user's initial message
                message_elements = Bot.extract_updates(updates)
                Bot.handle_updates(message_elements["first_name"], message_elements["chat_id"], message_elements["intent"], message_elements["message"])
        except Exception as e:
            print(e)

        time.sleep(0.5)
        sys.stdout.write('.'); sys.stdout.flush()

if __name__ == '__main__':
    main()
