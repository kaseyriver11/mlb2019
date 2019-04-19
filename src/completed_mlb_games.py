""" Script should run each morning at 5am. It looks for completed MLB games and adds them to the completed games
    database. It then looks for any bets placed on these games in the bets database, and checks how we did. """

import requests
from bs4 import BeautifulSoup
from pandas import DataFrame, read_sql

import sys
sys.path.append('')

try:
    from src.functions import *
except ModuleNotFoundError:
    raise


def create_results(rows):
    new_rows = []
    for i, row in enumerate(rows):
        # ----- Only look at completed games
        if len(row.find_all('', {'data-game-status': 'completed'})) > 0:
            # ----- If there is a game time, it is the first row of 2.
            gt = row.find('span', {'class': 'time'})
            if gt:
                # ----- Was the game yesterday?
                date = row.find('', {'class': 'day short'})
                if short_date_to_datetime(date, yesterday) == yesterday:
                    # ----- Game Time
                    game_time = convert_time(gt.text)
                    # ----- Winner
                    winner = row.find_all('', {'class': 'td number td-number score is-winner'})
                    if len(winner) > 0:
                        winner = 'away'
                    else:
                        winner = 'home'
                    # ----- Away Team, Score
                    a_team = row.find('span', {'class': 'team-name short'}).text
                    a_score = int(row.find('td', {'data-game-status': 'completed'}).text)

                    # ----- Home Team, Score
                    h_team = rows[i + 1].find('span', {'class': 'team-name short'}).text
                    h_score = int(rows[i + 1].find('td', {'data-game-status': 'completed'}).text)

                    # ----- Game ID
                    game_id = str(day_id) + "_" + a_team + '_' + h_team + "_" + str(game_time.hour)

                    new_rows.append([game_id, a_team, h_team, a_score, h_score, winner])

    return DataFrame(new_rows, columns=['id', 'away', 'home', 'away_score', 'home_score', 'winner'])


if __name__ == '__main__':

    # ----- Connect to the database
    db = setup_db()
    conn = db.connect()
    # ----- Extract contents from 538s baseball games
    r = requests.get("https://projects.fivethirtyeight.com/2019-mlb-predictions/games/")
    soup = BeautifulSoup(r.text, 'lxml')

    # ----- Find all rows in the soup
    soup_rows = soup.find_all('tr')
    # ----- Grab the results of these rows for completed games
    results = create_results(rows=soup_rows)

    # ----- STEP #1: Insert Games into the database
    if len(results) > 0:
        df_columns = list(results)
        # ----- Create (col1, col2, ...)
        columns = ",".join(df_columns)
        # ----- Create VALUES('%s', '%s",...) one '%s' per column
        values = "VALUES({})".format(",".join(["%s" for _ in df_columns]))
        # ----- Create insert statement
        insert_stmt = "INSERT INTO {} ({}) {}".format('game_outcome', columns, values)

        for result in results.iterrows():
            # --- Check if line is already in Database
            try:
                conn.execute(insert_stmt, result[1])
            except sqlalchemy.exc.IntegrityError:
                'nothing'

    # ----- STEP #2: Check if we made any bets on these games
    # ----- Grab any games from today already in the database
    query = '''
            SELECT id
            FROM games
            WHERE date = %(date)s
            '''
    # ----- Run query
    games = read_sql(query, db, params={'date': yesterday})

    # TODO
