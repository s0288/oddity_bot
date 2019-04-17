import pandas as pd
import numpy as np
import datetime
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt

# for loading the image and adding a border
from PIL import Image, ImageOps

from db_bot import DBBot

DBBot = DBBot()

### >>> connect to db <<< ###
import sys
sys.path.append('../')
import config
from sqlalchemy import *
engine = create_engine(config.POSTGRES)
metadata = MetaData(engine)
conn = engine.connect()



data = DBBot.get_active_users("telegram_ids_only")
ids = []
for num, id in enumerate(data):
    ids.append(data[num][0])

## change here if you want to get yesterday:
# for meal pics
#target_date = datetime.datetime.today().date()
target_date = datetime.datetime.today().date() - datetime.timedelta(days = 1)
# for polar plot:
day = 1

for user in ids:

    ##### >>>>> create polar plot <<<<< ######

    stmt = "SELECT * FROM key_values WHERE key_value in ('user_photo', 'meal_entry') AND telegram_id = {} ORDER BY created_at DESC".format(user)
    df = pd.read_sql_query(stmt, conn)
    df = np.array(df, dtype=object)

    polar_data = []
    times = []
    for row in enumerate(df):
        if user == row[1][1]:
            date = row[1][5].date()
            if date == (datetime.date.today() - datetime.timedelta(days=day)):
                time = row[1][5]
                time_since_midnight = (time - datetime.datetime.today().replace(hour=0, minute=0, second=0)).total_seconds()/60/60
                # calculate the decimal of the difference between 0:00 and the timestamp and see if the value is in the first or second half of the day
                if time_since_midnight < 12:
                    time = (12 - time_since_midnight)/12
                    for_polar = time*np.pi
                else:
                    time = (12 - time_since_midnight)/12
                    for_polar = time*np.pi
                times.append(time_since_midnight)
                polar_data.append(for_polar)

    try:
        # create polar plot
        r = np.ones(len(polar_data))*(len(polar_data)/100)#[1, 1, 1, 1] #np.arange(0, len(polar_data))
        fig = plt.figure()
        ax = plt.subplot(111,polar=True)
        ax.scatter(polar_data,r)
        ax.set_xticklabels(['      12:00', '', '06:00', '', '24:00      ', '', '18:00', ''])
        ax.set_yticklabels([])
        plt.title('Du hast innerhalb von {} Stunden gegessen'.format(round(max(times) - min(times), 2)), y=1.08)
        fig.savefig('../../../nad_app/user_files/polar_plots/{}_{}.png'.format(user, datetime.date.today() - datetime.timedelta(days=day)))
        plt.close(fig)
        print('created polar plot for {}'.format(user))
    except:
        fig.savefig('../../../nad_app/user_files/polar_plots/{}_{}.png'.format(user, datetime.date.today() - datetime.timedelta(days=day)))
        plt.close(fig)
        print("no data so far")



    ##### >>>>> create meal pic <<<<< ######
    # get the names of the user uploads
    # get the user_photos, meal_entries, meal_paths and meal_reasons
    stmt = "select * from key_values where telegram_id = {} and key_value in ('user_photo', 'meal_entry', 'meal_path', 'meal_reason') and date(created_at) = '{}' order by created_at asc".format(user, target_date)
    df = pd.read_sql_query(stmt, conn)

    ## assign paths and reasons to photos/entries
    imgs = []
    created_at = []
    paths = []
    reasons = []

    count_df = len(df)

    for num in range(count_df):
        # get image urls and created at
        if df["key_value"][num] in ('user_photo', 'meal_entry'):
            imgs.append("{}/{}_meal_entry_{}_{}_{}-{}-{}".format(str(df['created_at'][num].isocalendar()[0]) + "-" + str(df['created_at'][num].isocalendar()[1]), df['telegram_id'][num], df['key_value'][num], df['created_at'][num].date(), df['created_at'][num].hour, df['created_at'][num].minute, df['created_at'][num].second))
            created_at.append(df['created_at'][num])

            ## only check for paths and reasons, when the current input is an image
            # get meal paths
            if df["key_value"][min(num+1, count_df-1)] == 'meal_path':
                paths.append(df["value"][min(num+1, count_df-1)])
            else:
                paths.append(None)
            # get meal reasons
            if df["key_value"][min(num+2, count_df-1)] == 'meal_reason':
                reasons.append(df["value"][min(num+2, count_df-1)])
            else:
                reasons.append(None)


    ## set number of images for max for loop
    count_images = len(imgs)
    # assign number of rows and columns in the image
    if count_images <= 5:
        rows = 1
        cols = count_images
    elif count_images <= 10:
        rows = 2
        cols = 5
    elif count_images <= 15:
        rows = 3
        cols = 5
    else:
        print('way too many pics or no pics')
        rows = 0
        cols = 2

    fig = plt.figure(figsize=(12, 12))
    polar_img=Image.open("../../../nad_app/user_files/polar_plots/{}_{}.png".format(user, target_date))
    if count_images > 0:
        gridsize = (2 + rows, cols)
        ax = plt.subplot2grid(gridsize, (0, 0), colspan=cols, rowspan=2)
        ax.imshow(polar_img, aspect='equal')
        ax.set_xticks([])
        ax.set_yticks([])

        for num in range(count_images):
            try:
                img=Image.open("../../../nad_app/user_files/{}".format(imgs[num]))
            except:
                print('mealtime logged')
                img=Image.open("../../../nad_app/static/no_photo.jpg")

            if num < 5:
                row_index = 2
                col_index = num
            elif num < 10:
                row_index = 3
                col_index = num - 5

            ## add image border based on meal_path
            if paths[num]  == 'bringt mich näher':
                img_with_border = ImageOps.expand(img,border=75,fill='lime')
            elif paths[num]  == 'entfernt mich':
                img_with_border = ImageOps.expand(img,border=75,fill='orange')
            elif paths[num]  == 'weiß ich nicht':
                img_with_border = ImageOps.expand(img,border=75,fill='white')
            else:
                img_with_border = img


            locals()["ax"+str(num+1)] = plt.subplot2grid(gridsize, (row_index, col_index))
            locals()["ax"+str(num+1)].imshow(img_with_border, aspect='equal')
            # remove ticks on x and y axes
            locals()["ax"+str(num+1)].set_xticks([])
            locals()["ax"+str(num+1)].set_yticks([])
            # add time of meal as title
            locals()["ax"+str(num+1)].set_title("{} - {}:{}".format(created_at[num].date().strftime('%d-%m'), created_at[num].hour, created_at[num].minute))

            ## add reason based on meal_reason
            if reasons[num] is not None:
                locals()["ax"+str(num+1)].text(0.5,-0.1, (reasons[num][:25] + '..') if len(reasons[num]) > 25 else reasons[num], size=12, ha="center", transform=locals()["ax"+str(num+1)].transAxes)

    else:
        ax.imshow(polar_img, aspect='equal')
    fig.savefig('../../../nad_app/static/food/{}_{}.png'.format(user, datetime.datetime.strftime(target_date, '%y-%m-%d')))
    print('created meal pic for {}'.format(user))
    plt.close(fig)

conn.close()
print('closed connection: {}'.format(conn.closed))
