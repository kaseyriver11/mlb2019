# -*- coding: utf-8 -*-
"""
Created on Sun Apr 21 13:29:46 2019

@author: MH656TU
"""

import requests
from bs4 import BeautifulSoup
import time
from pandas import DataFrame, read_sql


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
    'ML': '',
    'RL': 'pointspread/',
    'total': 'totals/',
    '1H': '1st-half/',
    '1HRL': 'pointspread/1st-half/',
    '1Htotal': 'totals/1st-half/'
}


def soup_url(type_of_line):
    # get html code for odds based on desired line type and date
    url_addon = web_url[type_of_line]

    t_date = str(today).replace('-', '')
    url = 'https://classic.sportsbookreview.com/betting-odds/mlb-baseball/' + url_addon + '?date=' + t_date
    raw_data = requests.get(url)
    soup_big = BeautifulSoup(raw_data.text, 'html.parser')
    try:
        soup_final = soup_big.find_all('div', id='OddsGridModule_3')[0]
    except requests.exceptions.SSLError:
        soup_final = None
    timestamp = time.strftime("%H:%M:%S")
    return soup_final, timestamp


def clean_odds(string):
    final = string
    final = final.replace(u'\xa0', ' ').replace(u'\xbd', '.5') .replace("PK", "0 ")
    return final


def book_line(soup_flavor, book_id, line_id, homeaway):
    # Get Line info from book ID
    line = soup_flavor.find_all('div', attrs={'class': 'el-div eventLine-book',
                                              'rel': book_id})[line_id].find_all('div')[homeaway].get_text().strip()
    return line


def convert_time_sbr(x):
    in_time = x[:-1] + ' ' + x[-1:]
    in_time = dt.datetime.strptime(in_time.replace("p", "PM").replace("a", "AM"), "%I:%M %p").time()
    return in_time


def get_line_odds(soup_flavor):
    number_of_games = len(soup_flavor.find_all('div', attrs={'class': 'el-div eventLine-rotation'}))

    list_line_odds = []

    for i in range(0, number_of_games):
        print('getting game', str(i + 1) + '/' + str(number_of_games))

        game_time = convert_time_sbr(soup_flavor.find_all('div', attrs={'class': 'el-div eventLine-time'})
                                     [i].get_text())

        info_a = ' '.join(soup_flavor.find_all('div', attrs={'class': 'el-div eventLine-team'})
                          [i].find_all('div')[0].get_text().split())
        hyphen_a = info_a.find('-')
        team_a = info_a[:hyphen_a - 1]

        info_h = ' '.join(soup_flavor.find_all('div', attrs={'class': 'el-div eventLine-team'})
                          [i].find_all('div')[2].get_text().split())
        hyphen_h = info_h.find('-')
        team_h = info_h[:(hyphen_h - 1)]

        game_line_odds = []

        game_line_odds.extend([str(game_time.hour)])
        game_line_odds.extend([team_a])
        game_line_odds.extend([team_h])

        for book in bookID.values():
            a_line_odd = clean_odds(book_line(soup_flavor, book, i, 0)).split()
            h_line_odd = clean_odds(book_line(soup_flavor, book, i, 1)).split()
            if len(a_line_odd) == 0:
                game_line_odds.extend([None, None, None, None])
            elif len(a_line_odd) == 1:
                game_line_odds.extend([0, float(a_line_odd[0]), 0, float(h_line_odd[0])])
            else:
                game_line_odds.extend([float(a_line_odd[0]),
                                       float(a_line_odd[1]),
                                       float(h_line_odd[0]),
                                       float(h_line_odd[1])])

        list_line_odds.append(game_line_odds)

    df_line_odds = DataFrame.from_records(list_line_odds)
    df_line_odds.columns = ["game_hour",
                            "team_away",
                            "team_home",
                            "pinnac_line_a",
                            "pinnac_odds_a",
                            "pinnac_line_h",
                            "pinnac_odds_h",
                            "5dimes_line_a",
                            "5dimes_odds_a",
                            "5dimes_line_h",
                            "5dimes_odds_h",
                            "bookma_line_a",
                            "bookma_odds_a",
                            "bookma_line_h",
                            "bookma_odds_h",
                            "betonl_line_a",
                            "betonl_odds_a",
                            "betonl_line_h",
                            "betonl_odds_h",
                            "bovada_line_a",
                            "bovada_odds_a",
                            "bovada_line_h",
                            "bovada_odds_h",
                            "herita_line_a",
                            "herita_odds_a",
                            "herita_line_h",
                            "herita_odds_h",
                            "intert_line_a",
                            "intert_odds_a",
                            "intert_line_h",
                            "intert_odds_h",
                            "youwag_line_a",
                            "youwag_odds_a",
                            "youwag_line_h",
                            "youwag_odds_h",
                            "justbe_line_a",
                            "justbe_odds_a",
                            "justbe_line_h",
                            "justbe_odds_h",
                            "sports_line_a",
                            "sports_odds_a",
                            "sports_line_h",
                            "sports_odds_h"]
    return df_line_odds


def add_lines(df_series):
    return [item + 100 if item >= 0 else 100/(abs(item)/100) + 100 for item in df_series]


if __name__ == '__main__':
    soup_ml = None
    try:
        soup_ml, time_ml = soup_url('ML')
        print("getting today's MoneyLine (1/6)")
    except requests.exceptions.SSLError:
        print("couldn't get today's moneyline :(")

    df_ml = get_line_odds(soup_ml)
    df_ml.insert(0, "Odds_Type", "Money Line Full")
    df_ml.insert(0, "id", df_ml.apply(lambda x: '01' + '_' + str(day_id) + "_" + x.team_away +
                                                "_" + x.team_home + "_" + str(x.game_hour), axis=1))

    lines = df_ml[['id', 'pinnac_odds_a', 'pinnac_odds_h']]
    lines = lines.fillna(0)

    # ----- Get today's game from the database
    db = setup_db()
    conn = db.connect()
    query = '''
            SELECT m.id, m.a_chance_winning, m.h_chance_winning
            FROM games
            INNER JOIN mlb_538 as m
            ON games.id = m.id
            WHERE date = %(date)s
            '''
    # ----- Run query
    games = read_sql(query, db, params={'date': today})
    lines = lines.merge(games, on='id')
    lines['away_winnings'] = add_lines(lines['pinnac_odds_a'])
    lines['home_winnings'] = add_lines(lines['pinnac_odds_h'])
    lines['away_expected'] = lines['a_chance_winning'] * lines['away_winnings']
    lines['home_expected'] = lines['h_chance_winning'] * lines['home_winnings']

    # ----- Which games do we bet on?
    home_bets = lines[lines['home_expected'] > 102]
    away_bets = lines[lines['away_expected'] > 102]

    # ----- Insert these into the bets database






