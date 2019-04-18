
import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime as dt
import json
import sqlalchemy


# function to convert 538 game time formats to python datetime time
def convert_time(x):
    if len(x) > 7:
        in_time = dt.datetime.strptime(x.replace(".", ""), "%I:%M %p").time()
    else:
        in_time = dt.datetime.strptime(x.replace(".", ""), "%I %p").time()
    return in_time


url = "https://projects.fivethirtyeight.com/2019-mlb-predictions/games/"
r = requests.get(url)
soup = BeautifulSoup(r.text, 'lxml')

# What is today?
date = soup.find_all('span', {'class': 'day long'})
today = dt.datetime.today().strftime('%A, %B %d')
today2 = dt.datetime.today().strftime('%m_%d_%Y')
days = [item.text for item in date if item.text == today]

# ----- Game Time
game_time = soup.find_all('span', {'class': 'time'})
game_time = [convert_time(item.text) if len(item.text.split()) == 2 else
             convert_time(' '.join(item.text.split()[0:2])) for item in game_time for _ in range(2)]
# ----- Team Name
team_name = soup.find_all('span', {'class': 'team-name short'})
team_name = [item.text for item in team_name]
# ----- Starting pitcher
starting_pitcher = soup.find_all('', {'class': 'pitcher-img js-pitcher-img no-pitcher-img'})
starting_pitcher = [item['alt'] for item in starting_pitcher]
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
df['date'] = [dt.date.today()]*len(days)
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
df.insert(0, 'id', df.apply(lambda x: today2 + "_" + x['a_team_name'] + '_' + x['h_team_name'], axis=1))

# ----------------------------------------------------------------------------------------------------------------------
# ----- Setup credentials
with open('local/db_creds.prod', mode='rt') as f:
    db_creds = json.load(f)
# ----- Setup connection
db = sqlalchemy.create_engine('{dialect}://{user}:{password}@{host}:{port}/{dbname}'.format(**db_creds))
conn = db.connect()

# ----- Grab any games from today already in the database
query = '''
        SELECT *
        FROM games_538
        WHERE date = %(id)s
        '''
# ----- Run query
games = pd.read_sql(query, db, params={'id': dt.date.today()})

# ----- Are there any rows to add?
if len(df) > 0:
    df_columns = list(df)
    # ----- Create (col1,col2,...)
    columns = ",".join(df_columns)
    # ----- Create VALUES('%s', '%s",...) one '%s' per column
    values = "VALUES({})".format(",".join(["%s" for _ in df_columns]))
    # ----- Create insert statement
    insert_stmt = "INSERT INTO {} ({}) {}".format('games_538', columns, values)
    # ----- Create update statement
    update_away = """UPDATE games_538 SET a_chance_winning = %s WHERE id = %s"""
    update_home = """UPDATE games_538 SET h_chance_winning = %s WHERE id = %s"""

    """Update mobile set price = %s where id = %s"""
    for row in df.iterrows():
        if row[1].id not in games.id.values:
            conn.execute(insert_stmt, row[1])
        else:
            conn.execute(update_away, (row[1].a_chance_winning, row[1].id))
            conn.execute(update_home, (row[1].h_chance_winning, row[1].id))
