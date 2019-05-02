
import requests
from bs4 import BeautifulSoup
from pandas import DataFrame

import sys
sys.path.append('')

try:
    from src.functions import *
except ModuleNotFoundError:
    raise


def mlb_538(rows):
    new_rows = []
    for i, row in enumerate(rows):
        # ----- Only look at completed games
        if len(row.find_all('', {'data-game-status': 'upcoming'})) > 0:
            # ----- If there is a game time, it is the first row of 2.
            gt = row.find('span', {'class': 'time'})
            if gt:
                # ----- Is the game today?
                date = row.find('', {'class': 'day short'})
                if short_date_to_datetime(date, today) == today:
                    game_time = convert_time(gt.text)
                    # ----- Away Team
                    away = list()
                    away.append(row.find('span', {'class': 'team-name short'}).text)
                    away.append(row.find('', {'class': 'pitcher-img js-pitcher-img no-pitcher-img'})['alt'])
                    away.append(int(row.find('td', {'class': 'td number td-number rating'}).text))
                    away.append(make_int(row.find('td', {'class': 'td number td-number pitcher-adj'})))
                    away.append(make_int(row.find('td', {'class': 'td number td-number travel-adj'})))
                    away.append(int(row.find('td', {'class': 'td number td-number rating-adj'}).text[1:]))
                    away.append(float(row.find('td', {'class': 'td number td-number win-prob'}).text[:-1])/100)
                    # ----- Home Team
                    r2 = rows[i+1]
                    home = list()
                    home.append(r2.find('span', {'class': 'team-name short'}).text)
                    home.append(r2.find('', {'class': 'pitcher-img js-pitcher-img no-pitcher-img'})['alt'])
                    home.append(int(r2.find('td', {'class': 'td number td-number rating'}).text))
                    home.append(make_int(r2.find('td', {'class': 'td number td-number pitcher-adj'})))
                    home.append(make_int(r2.find('td', {'class': 'td number td-number travel-adj'})))
                    home.append(int(r2.find('td', {'class': 'td number td-number rating-adj'}).text[1:]))
                    home.append(float(r2.find('td', {'class': 'td number td-number win-prob'}).text[:-1])/100)

                    game_id = '01' + '_' + str(day_id) + "_" + away[0] + "_" + home[0] + "_" + str(game_time.hour)

                    new_rows.append([game_id, today, game_time] + away + home)

    return DataFrame(new_rows,
                     columns=['id', 'date', 'game_time',
                              'away', 'away_starting_pitcher', 'away_team_rating', 'away_starting_pitcher_adjustment',
                              'away_travel_adjustment', 'away_pregame_rating', 'away_chance_winning',
                              'home', 'home_starting_pitcher', 'home_team_rating', 'home_starting_pitcher_adjustment',
                              'home_travel_adjustment', 'home_pregame_rating', 'home_chance_winning'])


if __name__ == '__main__':

    # ----- Connect to the database
    db = setup_db()
    conn = db.connect()

    # ---- Make the soup
    url = "https://projects.fivethirtyeight.com/2019-mlb-predictions/games/"
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'lxml')

    # ----- Find all rows in the soup, and grab the days games
    soup_rows = soup.find_all('tr')
    df = mlb_538(soup_rows)

    # ----- STEP #1: Insert Games into the games table
    if len(df) > 0:
        names = ['id', 'sport', 'date', 'game_time', 'away', 'home']
        columns = ",".join(names)
        values = "VALUES({})".format(",".join(["%s" for _ in names]))
        # ----- Create insert statement
        insert_stmt = "INSERT INTO {} ({}) {}".format('games', columns, values)

        for new_game in df.iterrows():
            value = [new_game[1].id, 'MLB', new_game[1].date, new_game[1].game_time, new_game[1].away, new_game[1].home]
            # --- Check if line is already in Database
            try:
                conn.execute(insert_stmt, value)
            except sqlalchemy.exc.IntegrityError as e:
               print(e)
    else:
        print('ERROR: no games were found')

    # ----- STEP #2: Insert Games in the mlb_538 table
    mlb_data = df.drop(['away', 'home', 'date', 'game_time'], axis=1)
    if len(df) > 0:
        mlb_columns = mlb_data.columns
        # ----- Create (col1,col2,...)
        columns = ",".join(mlb_columns)
        # ----- Create VALUES('%s', '%s",...) one '%s' per column
        values = "VALUES({})".format(",".join(["%s" for _ in mlb_columns]))
        # ----- Create insert statement
        insert_stmt = "INSERT INTO {} ({}) {}".format('mlb_538', columns, values)
        # ----- Create update statement
        update_away = """UPDATE mlb_538 SET away_chance_winning = %s WHERE id = %s"""
        update_home = """UPDATE mlb_538 SET home_chance_winning = %s WHERE id = %s"""

        """Update mobile set price = %s where id = %s"""
        for game in mlb_data.iterrows():
            try:
                conn.execute(insert_stmt, game[1])
            except sqlalchemy.exc.IntegrityError:
                conn.execute(update_away, (game[1].away_chance_winning, game[1].id))
                conn.execute(update_home, (game[1].home_chance_winning, game[1].id))
