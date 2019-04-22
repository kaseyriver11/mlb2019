# -*- coding: utf-8 -*-
"""
Created on Sun Apr 21 13:29:46 2019

@author: MH656TU
"""

import requests
from bs4 import BeautifulSoup
#import datetime
from datetime import date
import time
import pandas as pd
from pandas import DataFrame
import datetime as dt


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
        "SportsBetting": '999991'}

bookID_list = list(bookID.values())

def soup_url(type_of_line, tdate = str(date.today()).replace('-','')):
## get html code for odds based on desired line type and date

    web_url = dict()
    web_url['ML'] = ''
    web_url['RL'] = 'pointspread/'
    web_url['total'] = 'totals/'
    web_url['1H'] = '1st-half/'
    web_url['1HRL'] = 'pointspread/1st-half/'
    web_url['1Htotal'] = 'totals/1st-half/'
    url_addon = web_url[type_of_line]

    url = 'https://classic.sportsbookreview.com/betting-odds/mlb-baseball/' + url_addon + '?date=' + tdate
    raw_data = requests.get(url)
    soup_big = BeautifulSoup(raw_data.text, 'html.parser')
    try:
        soup_final = soup_big.find_all('div', id='OddsGridModule_3')[0]
    except:
        soup_final = None
    timestamp = time.strftime("%H:%M:%S")
    return soup_final, timestamp


def clean_odds(string):
    final = string
    final = final.replace(u'\xa0',' ').replace(u'\xbd','.5') .replace("PK","0 ")
    return final

def book_line(soup_flavor, book_id, line_id, homeaway):
    ## Get Line info from book ID
    line = soup_flavor.find_all('div', attrs = {'class':'el-div eventLine-book', 'rel':book_id})[line_id].find_all('div')[homeaway].get_text().strip()
    return line


todays_date = str(date.today()).replace('-','')



try:
    soup_ml, time_ml = soup_url('ML', todays_date)
    print("getting today's MoneyLine (1/6)")
except:
    print("couldn't get today's moneyline :(")

try:
    soup_rl, time_rl = soup_url('RL', todays_date)
    print("getting today's RunLine (2/6)")
except:
    print("couldn't get today's runline :(")

try:
    soup_tot, time_tot = soup_url('total', todays_date)
    print("getting today's totals (3/6)")
except:
    print("couldn't get today's totals :(")

try:
    soup_1h_ml, time_1h_ml = soup_url('1H', todays_date)
    print("getting today's 1st-half MoneyLine (4/6)")
except:
    soup_1h_ml = ''
    time_1h_ml = ''
    print("couldn't get today's 1h ml :(")

try:
    soup_1h_rl, time_1h_rl = soup_url('1HRL', todays_date)
    print("getting today's 1st-half RunLine (5/6)")
except:
    soup_1h_rl = ''
    time_1h_rl = ''
    print("couldn't get today's 1h rl :(")

try:
    soup_1h_tot, time_1h_tot = soup_url('1Htotal', todays_date)
    print("getting today's 1st-half totals (6/6)")
except:
    soup_1h_tot = ''
    time_1h_tot = ''
    print("couldn't get today's 1h totals :(")



def convert_time_sbr(x):
    in_time = x[:-1] + ' ' + x[-1:]
    in_time = dt.datetime.strptime(in_time.replace("p", "PM").replace("a", "AM"), "%I:%M %p").time()
    return in_time



def get_line_odds(soup_flavor):
    
    number_of_games = len(soup_flavor.find_all('div', attrs = {'class':'el-div eventLine-rotation'}))
    
    list_line_odds = []
    
    for i in range(0, number_of_games):
        print('getting game',str(i+1)+'/'+str(number_of_games))
        
        game_time = convert_time_sbr(soup_flavor.find_all('div', attrs = {'class':'el-div eventLine-time'})[i].get_text())
        
        info_A = ' '.join(soup_flavor.find_all('div', attrs = {'class':'el-div eventLine-team'})[i].find_all('div')[0].get_text().split())
        hyphen_A = info_A.find('-')
        paren_A = info_A.find("(")
        team_A = info_A[:hyphen_A - 1]
        pitcher_A = info_A[hyphen_A + 2 : paren_A - 1]
        hand_A = info_A[paren_A + 1 : -1]
    
        info_H = ' '.join(soup_flavor.find_all('div', attrs = {'class':'el-div eventLine-team'})[i].find_all('div')[2].get_text().split())
        hyphen_H = info_H.find('-')
        paren_H = info_H.find("(")
        team_H = info_H[:hyphen_H - 1]
        pitcher_H = info_H[hyphen_H + 2 : paren_H - 1]
        hand_H = info_H[paren_H + 1 : -1]

        game_line_odds = []

        game_line_odds.extend([str(game_time.hour)])
        game_line_odds.extend([team_A])
        game_line_odds.extend([team_H])

        #print(str(game_time.hour))
        #print(team_A)
        #print(team_H)

        for book in bookID_list:
            A_line_odd = clean_odds(book_line(soup_flavor, book, i, 0)).split()
            H_line_odd = clean_odds(book_line(soup_flavor, book, i, 1)).split()
            if len(A_line_odd) == 0:
                game_line_odds.extend([None, None, None, None])        
            elif len(A_line_odd) == 1:
                game_line_odds.extend([0, float(A_line_odd[0]), 0, float(H_line_odd[0])])
            else:
                game_line_odds.extend([float(A_line_odd[0]),
                                       float(A_line_odd[1]),
                                       float(H_line_odd[0]),
                                       float(H_line_odd[1])])
    
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



df_line_odds_ml = get_line_odds(soup_ml)
df_line_odds_rl = get_line_odds(soup_rl)
df_line_odds_tot = get_line_odds(soup_tot)
df_line_odds_1h_ml = get_line_odds(soup_1h_ml)
df_line_odds_1h_rl = get_line_odds(soup_1h_rl)
df_line_odds_1h_tot = get_line_odds(soup_1h_tot)

df_line_odds_ml.insert(0, "Odds_Type", "Money Line Full")
df_line_odds_rl.insert(0, "Odds_Type", "Run Line Full")
df_line_odds_tot.insert(0, "Odds_Type", "Totals Full")
df_line_odds_1h_ml.insert(0, "Odds_Type", "Money Line Half")
df_line_odds_1h_rl.insert(0, "Odds_Type", "Run Line Half")
df_line_odds_1h_tot.insert(0, "Odds_Type", "Totals Half")

df_line_odds_ALL = pd.concat([df_line_odds_ml,
                              df_line_odds_rl,
                              df_line_odds_tot,
                              df_line_odds_1h_ml,
                              df_line_odds_1h_rl,
                              df_line_odds_1h_tot])


print(df_line_odds_ALL.intert_line_a.dtype)
print(df_line_odds_ALL.herita_line_a.dtype)