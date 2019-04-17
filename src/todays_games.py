# -*- coding: utf-8 -*-
"""
Created on Fri Apr 14 16:24:11 2017
@author: kaseyriver11
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime as dt
from datetime import datetime
import json
import sqlalchemy

url = "https://projects.fivethirtyeight.com/2019-mlb-predictions/games/"
r = requests.get(url)
soup = BeautifulSoup(r.text, 'lxml')

# What is today?
date = soup.find_all('span', {'class': 'day long'})
today = dt.datetime.today().strftime('%A, %B %d')
today2 = dt.datetime.today().strftime('%Y_%m_%d_')
days = [item.text for item in date if item.text == today]

# function to convert 538 game time formats to python datetime time
def convert_time(x):
    if len(x) > 7:
        in_time = datetime.strptime(x.replace(".",""), "%I:%M %p").time()
    else:
        in_time = datetime.strptime(x.replace(".",""), "%I %p").time()
    return in_time

# ----- Game Time
game_time = soup.find_all('span', {'class': 'time'})
game_time = [convert_time(item.text) if len(item.text.split()) == 2 else convert_time(' '.join(item.text.split()[0:2])) for item in game_time for _ in range(2)]
# ----- Team Name
team_name = soup.find_all('span', {'class': 'team-name short'})
team_name = [item.text for item in team_name]
# ----- Starting pitcher
starting_pitcher = soup.find_all('img', alt = True)
starting_pitcher = [item['alt'] for item in starting_pitcher][32::2]
# ----- Team Rating
team_rating = soup.find_all('td', {'class': 'td number td-number rating'})
team_rating = [int(item.text) for item in team_rating]
# ----- Starting Pitcher Adjustment
spa = soup.find_all('td', {'class': 'td number td-number pitcher-adj'})
starting_pitcher_adjustment = [int(item.text) if item.text[0] != '–' else int(item.text[1:])*-1 for item in spa]
# ----- Travel Adjustment
travel_adjustment = soup.find_all('td', {'class': 'td number td-number travel-adj'})
travel_adjustment = [int(item.text) if item.text[0] != '–' else int(item.text[1:])*-1 for item in travel_adjustment]
# ----- Pregame Rating
pregame_rating = soup.find_all('td', {'class': 'td number td-number rating-adj'})
pregame_rating = [int(item.text[1:]) for item in pregame_rating]
# ----- Chance of Winning
chance_winning = soup.find_all('td', {'class': 'td number td-number win-prob'})
chance_winning = [float(item.text[:-1])/100 for item in chance_winning]

df = pd.DataFrame()
df['game_time'] = game_time[0:len(days)*2:2]
df['a_team_name'] = team_name[0:len(days)*2:2]
df['a_starting_pitcher'] = starting_pitcher[0:len(days)*2:2]
df['a_team_rating'] = team_rating[0:len(days)*2:2]
df['a_starting_pitcher_adjustment'] = starting_pitcher_adjustment[0:len(days)*2:2]
df['a_travel_adjustment'] = travel_adjustment[0:len(days)*2:2]
df['a_pregame_rating'] = pregame_rating[0:len(days)*2:2]
df['a_chance_winning'] = chance_winning[0:len(days)*2:2]
df['h_team_name'] = team_name[1:(len(days)*2+1):2]
df['h_starting_pitcher'] = starting_pitcher[1:(len(days)*2+1):2]
df['h_team_rating'] = team_rating[1:(len(days)*2+1):2]
df['h_starting_pitcher_adjustment'] = starting_pitcher_adjustment[1:(len(days)*2+1):2]
df['h_travel_adjustment'] = travel_adjustment[1:(len(days)*2+1):2]
df['h_pregame_rating'] = pregame_rating[1:(len(days)*2+1):2]
df['h_chance_winning'] = chance_winning[1:(len(days)*2+1):2]
df.insert(0, 'id', df.apply(lambda x: today2 + x['a_team_name'] + '_' + x['h_team_name'], axis=1))

# ----------------------------------------------------------------------------------------------------------------------
# ----- Setup credentials
with open('local/db_creds.prod', mode='rt') as f:
    db_creds = json.load(f)
# ----- Setup connection
db = sqlalchemy.create_engine('{dialect}://{user}:{password}@{host}:{port}/{dbname}'.format(**db_creds))
conn = db.connect()


# df is the dataframe
if len(df) > 0:
    df_columns = list(df)
    # create (col1,col2,...)
    columns = ",".join(df_columns)

    # create VALUES('%s', '%s",...) one '%s' per column
    values = "VALUES({})".format(",".join(["%s" for _ in df_columns]))

    # create INSERT INTO table (columns) VALUES('%s',...)
    insert_stmt = "INSERT INTO {} ({}) {}".format('games_538', columns, values)

    for row in df.iterrows():
        conn.execute(insert_stmt, row[1])


# ---- Did it work?
query = '''
        SELECT *
        FROM games_538
        '''
# ----- Run query
games = pd.read_sql(query, db)
