# -*- coding: utf-8 -*-
"""
Created on Sun Apr 14 18:29:56 2019

@author: MH656TU
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd


url = r'https://projects.fivethirtyeight.com/2019-mlb-predictions/games/'
page = requests.get(url).text
soup = BeautifulSoup(page, 'lxml')

#soupPrettify = soup.prettify()

# find first <table class='table> which is a table of upcoming games; second <table class='table> is a table of completed games
table = soup.find('table',{'class':'table'})


tr = table.find_all('tr')
len(tr)


header = []
for x in tr[0]:
    header.append(x.get_text())
header.insert(1, "Time")
header = header[0:-1]


data = []

for x in range(1, len(tr)):
    span = tr[x].find_all('span')
    td = tr[x].find_all('td') 
    if len(tr[x].find_all('span')) == 13:
        date = span[0].get_text()
        time = span[2].get_text()
        team = span[4].get_text()
        stPi = span[6].get_text()
        teRa = td[3].get_text()
        stPiAd = span[7].get_text() + span[8].get_text()
        trReHoAd = span[9].get_text() + span[10].get_text()
        prTeRa = span[12].get_text()
        WiPr = td[7].get_text()
    elif len(tr[x].find_all('span')) == 9:
        team = span[0].get_text()
        stPi = span[2].get_text()
        teRa = td[2].get_text()
        stPiAd = span[3].get_text() + span[4].get_text()
        trReHoAd = span[5].get_text() + span[6].get_text()
        prTeRa = span[8].get_text()
        WiPr = td[6].get_text()
    sublist = [date, time, team, stPi, teRa, stPiAd, trReHoAd, prTeRa, WiPr]
    data.append(sublist)


data_df = pd.DataFrame(data, columns=header)