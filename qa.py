import pandas as pd
import numpy as np
import config
import os

file = input("QA for dialogue (type 'all' to check every saved dialogue): ")

#set up error log
error_log = []

# check specific dialogue
if file != 'all':
    data = pd.read_csv("{}/dialogues/{}.csv".format(config.DIRECTORY, file), dtype= str, delimiter=',')
    data = data.where(pd.notnull(data), None)
    f = lambda x: x.split("; ") if x is not None else x
    data["keyboard"] = data["keyboard"].apply(f)

    # get morten's dialogue options and the user's answer options
    dialogue_morten = []
    dialogue_user = []
    answer_morten = []
    answer_user = []
    for num, row in enumerate(data["message"]):
        # dialogue options
        if data["intent"][num] != 'end_conversation':
            if data["keyboard"][num] is not None:
                # add the catch-all answer that is always required
                if len(data["keyboard"][num]) > 200:
                    print('{} - too many chars when Morten says: {}'.format(file, dialogue_options["morten"][i]))
                dialogue_morten.append(data["message"][num])
                dialogue_user.append('✏')
                # get the specific dialogue options
                for i in range(0,len(data["keyboard"][num])-1):
                    dialogue_morten.append(data["message"][num])
                    dialogue_user.append(data["keyboard"][num][i])
            else:
                # if no keyboard is provided, just get the catch-all
                dialogue_morten.append(data["message"][num])
                dialogue_user.append('✏')
        # answer options
        answer_morten.append(data["last_bot_message"][num])
        answer_user.append(data['last_user_message'][num])
        # check if missing intent
        if data["intent"][num] is None:
            error_log.append('{} - no intent when Morten says: {}'.format(file, dialogue_options["morten"][i]))

    dialogue_options = pd.DataFrame({'morten': dialogue_morten,'user': dialogue_user})
    answer_options = pd.DataFrame({'morten': answer_morten,'user': answer_user})

    for i in range(0, len(dialogue_options)):
        if sum(((dialogue_options["morten"][i] == answer_options["morten"]) & (dialogue_options["user"][i] == answer_options["user"])) | ((dialogue_options["morten"][i] == answer_options["morten"]) & ('✏' == answer_options["user"]))) == 0:
            error_log.append('{} - error when Morten says: {}'.format(file, dialogue_options["morten"][i]))
        elif (len(dialogue_options['morten'][i]) > 200):
            error_log.append('{} - too many chars when Morten says: {}'.format(file, dialogue_options["morten"][i]))

    ## check if a dialogue doesn't end where it should
        data=np.array(data)
        uniques_dialogue_options = np.unique(dialogue_options["morten"])
        check_intent_for = []
        # create a list of dialogue options that don't have an answer option
        for num, row in enumerate(uniques_dialogue_options):
            if sum(uniques_dialogue_options[num] == np.array(answer_options["morten"])) == 0:
                check_intent_for.append(row)
        # check if the intent of the items in check_intent_for is 'end_conversation'
        for num, row in enumerate(check_intent_for):
            if data[(check_intent_for[num] == data[:,2])][0][8] != 'end_conversation':
                error_log.append('{} - dialogue does not end where it should: {}'.format(file, check_intent_for[num]))

# check all dialogues
else:
    file_identifiers = os.listdir("{}/dialogues/".format(config.DIRECTORY))
    #remove hidden files
    file_identifiers = [i for i in file_identifiers if i.endswith('.csv')]
    #remove extension
    file_identifiers = [os.path.splitext(each)[0] for each in file_identifiers]
    for file in file_identifiers:
        data = pd.read_csv("{}/dialogues/{}.csv".format(config.DIRECTORY, file), dtype= str, delimiter=',')
        data = data.where(pd.notnull(data), None)
        f = lambda x: x.split("; ") if x is not None else x
        data["keyboard"] = data["keyboard"].apply(f)

        # get morten's dialogue options and the user's answer options
        dialogue_morten = []
        dialogue_user = []
        answer_morten = []
        answer_user = []
        for num, row in enumerate(data["message"]):
            # dialogue options
            if data["intent"][num] != 'end_conversation':
                if data["keyboard"][num] is not None:
                    # add the catch-all answer that is always required
                    if len(data["keyboard"][num]) > 200:
                        print('{} - too many chars when Morten says: {}'.format(file, dialogue_options["morten"][i]))
                    dialogue_morten.append(data["message"][num])
                    dialogue_user.append('✏')
                    # get the specific dialogue options
                    for i in range(0,len(data["keyboard"][num])-1):
                        dialogue_morten.append(data["message"][num])
                        dialogue_user.append(data["keyboard"][num][i])
                else:
                    # if no keyboard is provided, just get the catch-all
                    dialogue_morten.append(data["message"][num])
                    dialogue_user.append('✏')
            # answer options
            answer_morten.append(data["last_bot_message"][num])
            answer_user.append(data['last_user_message'][num])
            # check if missing intent
            if data["intent"][num] is None:
                error_log.append('{} - no intent when Morten says: {}'.format(file, dialogue_options["morten"][i]))

        dialogue_options = pd.DataFrame({'morten': dialogue_morten,'user': dialogue_user})
        answer_options = pd.DataFrame({'morten': answer_morten,'user': answer_user})


        for i in range(0, len(dialogue_options)):
            if sum(((dialogue_options["morten"][i] == answer_options["morten"]) & (dialogue_options["user"][i] == answer_options["user"])) | ((dialogue_options["morten"][i] == answer_options["morten"]) & ('✏' == answer_options["user"]))) == 0:
                error_log.append('{} - error when Morten says: {}'.format(file, dialogue_options["morten"][i]))
            elif (len(dialogue_options['morten'][i]) > 200):
                error_log.append('{} - too many chars when Morten says: {}'.format(file, dialogue_options["morten"][i]))


# remove duplicates
def remove_duplicates(values):
    output = []
    seen = set()
    for value in values:
        # If value has not been encountered yet,
        # ... add it to both list and set.
        if value not in seen:
            output.append(value)
            seen.add(value)
    return output
error_log = remove_duplicates(error_log)

# print errors
for num, row in enumerate(error_log):
    print(error_log[num])
