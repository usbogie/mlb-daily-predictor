import pandas as pd
import json
import os
import time
import datetime
import random
from operator import itemgetter
from scrapers.scraper_utils import get_soup, team_codes

def get_todays_rosters():
    soup = get_soup('https://www.rosterresource.com/mlb-san-francisco-giants')
    print(soup.find('iframe')['src'].replace('/pubhtml', '/pubhtml/sheet'))
    new_soup = get_soup(soup.find('iframe')['src'].replace('/pubhtml', '/pubhtml/sheet'))
    trs = new_soup.find('tbody').findAll('tr')
    started_bullpen = False
    counter = 0
    for ix, tr in enumerate(trs):
        if tr.find('td', {'class': 's88'}) and 'Bullpen' in tr.find('td', {'class': 's88'}).text:
            started_bullpen = True
        if started_bullpen:
            counter = 1 + counter
            if counter <= 4:
                continue
            print(tr.find('td', {'class': 'softmerge'}))
