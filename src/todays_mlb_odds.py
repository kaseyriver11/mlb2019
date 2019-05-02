# -*- coding: utf-8 -*-
"""
Created on Sun Apr 21 13:29:46 2019

@author: MH656TU
"""

import requests
from bs4 import BeautifulSoup
from pandas import DataFrame, read_sql, Series

import sys
sys.path.append('')

try:
    from src.functions import *
except ModuleNotFoundError:
    raise


bookID = {
    "Pinnacle": '238',
    "5Dimes": '19',
    "Bookmaker": '93',
    "BetOnline": '1096',
    "Bovada": '999996',
    "Heritage": '169',
    "Intertops": '180',
    "Youwager": '139',
    "JustBet": '1275',
    "SportsBetting": '999991'
}

web_url = {
    'ML': ''
}


def extract_sportsbookreview_soup(type_of_line='ML'):
    """ Extract the soup from sports book review

    Parameters
    ----------
    type_of_line : str
        The type of lines you want pulled. Default: 'ML"

    Returns
    -------
    soup_final : bs4 element

    """
    url_addon = web_url[type_of_line]

    t_date = str(today).replace('-', '')
    url = 'https://classic.sportsbookreview.com/betting-odds/mlb-baseball/' + url_addon + '?date=' + t_date
    raw_data = requests.get(url)
    soup_big = BeautifulSoup(raw_data.text, 'html.parser')
    try:
        soup_final = soup_big.find_all('div', id='OddsGridModule_3')[0]
    except requests.exceptions.SSLError:
        soup_final = None

    return soup_final


def clean_odds(string):
    """ Remove the unicode spacing from a string"""
    return string.replace(u'\xa0', ' ').replace(u'\xbd', '.5') .replace("PK", "0 ")


def book_line(soup_flavor, book_id, line_id, home_away):
    """
    Parameters
    ----------
    soup_flavor :
        The soup of interest
    book_id : str
        The sports book id from the bookID dictionary
    line_id : int
        The game number
    home_away : int
        0 for away, 1 for home

    Return
    ------
    line : The book line
    """
    line = soup_flavor.find_all('div', attrs={'class': 'el-div eventLine-book',
                                              'rel': book_id})[line_id].find_all('div')[home_away].get_text().strip()
    return line


def convert_time_sbr(x):
    """ Convert the time into a sports book review friendly format"""
    in_time = x[:-1] + ' ' + x[-1:]
    in_time = dt.datetime.strptime(in_time.replace("p", "PM").replace("a", "AM"), "%I:%M %p").time()
    return in_time


def get_line_odds(soup_flavor):
    """ The the odds from each game in the soup"""
    number_of_games = len(soup_flavor.find_all('div', attrs={'class': 'el-div eventLine-rotation'}))
    list_line_odds = []

    for i in range(0, number_of_games):
        print('getting game', str(i + 1) + '/' + str(number_of_games))

        game_time = convert_time_sbr(soup_flavor.find_all('div', attrs={'class': 'el-div eventLine-time'})
                                     [i].get_text())

        info_away = ' '.join(soup_flavor.find_all('div', attrs={'class': 'el-div eventLine-team'})
                             [i].find_all('div')[0].get_text().split())
        team_away = info_away[0:info_away.find(" ")]

        info_home = ' '.join(soup_flavor.find_all('div', attrs={'class': 'el-div eventLine-team'})
                             [i].find_all('div')[2].get_text().split())
        team_home = info_home[0:info_home.find(" ")]

        game_line_odds = list()
        game_line_odds.append(str(game_time.hour))
        game_line_odds.append(team_away)
        game_line_odds.append(team_home)

        for book in bookID.values():
            away_line_odd = clean_odds(book_line(soup_flavor, book, i, 0)).split()
            home_line_odd = clean_odds(book_line(soup_flavor, book, i, 1)).split()
            if len(away_line_odd) == 0:
                game_line_odds.extend([None, None])
            elif len(away_line_odd) == 1:
                game_line_odds.extend([float(away_line_odd[0]), float(home_line_odd[0])])
            else:
                game_line_odds.extend([float(away_line_odd[1]), float(home_line_odd[1])])

        list_line_odds.append(game_line_odds)

    df_line_odds = DataFrame.from_records(list_line_odds)
    column_names = ['game_hour', 'team_away', 'team_home']
    for i in bookID:
        column_names.extend([i + 'odds_a', i + 'odds_h'])
    df_line_odds.columns = column_names
    return df_line_odds


def add_lines(df_series):
    return [item + 100 if item >= 0 else 100/(abs(item)/100) + 100 for item in df_series]


if __name__ == '__main__':
    soup_ml = None
    try:
        soup_ml = extract_sportsbookreview_soup('ML')
        print("getting today's MoneyLine")
    except requests.exceptions.SSLError:
        print("couldn't get today's money line")

    if soup_ml:
        df_ml = get_line_odds(soup_ml)
        df_ml.insert(0, "id", df_ml.apply(lambda x: '01' + '_' + str(day_id) + "_" + x.team_away +
                                                    "_" + x.team_home + "_" + str(x.game_hour), axis=1))
        df_ml = df_ml.fillna(0)

        # ----- Get today's game from the database
        db = setup_db()
        conn = db.connect()
        query = '''
                SELECT m.id, g.game_time, m.away_chance_winning, m.home_chance_winning
                FROM games as g
                INNER JOIN mlb_538 as m
                ON g.id = m.id
                WHERE date = %(date)s
                '''
        # ----- Run query
        games = read_sql(query, db, params={'date': today})
        # ----- Filter to games that haven't started
        games = games[[item.hour > dt.datetime.now().hour for item in games['game_time']]]
        # ----- Only continue if games exist
        if games.shape[0] != 0:
            lines = df_ml.merge(games, on='id')
            # ----- Find the best book to place a home and an away bet at:
            away_books = [item for item in lines.columns if 'odds_a' in item]
            away_best, away_sports_book, away_odds = list(), list(), list()
            for game in lines[away_books].iterrows():
                values = add_lines(Series(game[1]))
                away_best.append(max(values))
                away_sports_book.append(away_books[values.index(max(values))].replace('odds_a', ''))
                away_odds.append(game[1].values[values.index(max(values))])
            home_books = [item for item in lines.columns if 'odds_h' in item]
            home_best, home_sports_book, home_odds = list(), list(), list()
            for game in lines[home_books].iterrows():
                values = add_lines(Series(game[1]))
                home_best.append(max(values))
                home_sports_book.append(home_books[values.index(max(values))].replace('odds_h', ''))
                home_odds.append(game[1].values[values.index(max(values))])

            final_lines = lines[['id', 'away_chance_winning', 'home_chance_winning']].copy()
            final_lines['away_winnings'] = away_best
            final_lines['home_winnings'] = home_best
            final_lines['away_sports_book'] = away_sports_book
            final_lines['home_sports_book'] = home_sports_book
            final_lines['away_expected'] = final_lines['away_chance_winning'] * final_lines['away_winnings']
            final_lines['home_expected'] = final_lines['home_chance_winning'] * final_lines['home_winnings']
            final_lines['away_odds'] = away_odds
            final_lines['home_odds'] = home_odds

            # ----- Which games do we bet on?
            home_bets = final_lines[final_lines['home_expected'] > 101]
            away_bets = final_lines[final_lines['away_expected'] > 101]

            # ----- Find any game already bet on - do not bet on these games
            # ----- Get today's game from the database
            query = '''
                    SELECT m.id
                    FROM games as g
                    INNER JOIN placed_bets as m
                    ON g.id = m.id
                    WHERE date = %(date)s
                    '''
            # ----- Run query
            bets = read_sql(query, db, params={'date': today})

            # ---- Setup insert
            names = ['id', 'sports_book', 'bet_on', 'amount_bet', 'odds_bet', 'chance_to_win', 'to_win',
                     'expected_winnings']
            columns = ",".join(names)
            values = "VALUES({})".format(",".join(["%s" for _ in names]))
            insert_stmt = "INSERT INTO {} ({}) {}".format('placed_bets', columns, values)

            # ----- Place Bets: Away
            if away_bets.shape[0] > 0:
                for game in away_bets.iterrows():
                    if game[1].id not in bets.values:
                        insert_values = [game[1].id, game[1].away_sports_book, 'away', 100, game[1].away_odds,
                                         game[1].away_chance_winning, game[1].away_winnings, game[1].away_expected]
                        conn.execute(insert_stmt, insert_values)
            # ----- Place Bets: Home
            if home_bets.shape[0] > 0:
                for game in home_bets.iterrows():
                    if game[1].id not in bets.values:
                        insert_values = [game[1].id, game[1].home_sports_book, 'home', 100, game[1].home_odds,
                                         game[1].home_chance_winning, game[1].home_winnings, game[1].home_expected]
                        conn.execute(insert_stmt, insert_values)

        else:
            print('ERROR: no games were found.')
