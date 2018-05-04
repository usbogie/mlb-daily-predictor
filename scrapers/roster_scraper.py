import pandas as pd
import json
import os
import time
import datetime
import random
from operator import itemgetter
from scrapers.scraper_utils import get_soup, team_codes

def get_team_roster(team):
    print(team)
    soup = get_soup('https://www.rosterresource.com/mlb-{}'.format(team))
    new_soup = get_soup(soup.find('iframe')['src'].replace('/pubhtml', '/pubhtml/sheet'))
    trs = new_soup.find('tbody').findAll('tr')
    started_bullpen = False
    counter = 0
    pitchers = []
    for ix, tr in enumerate(trs):
        tds = tr.findAll('td')
        for td in tds:
            if 'Bullpen' in td.text:
                started_bullpen = True
        if started_bullpen:
            counter = 1 + counter
            if counter <= 4:
                continue
            if len(tds[2].text.strip()) == 0:
                break
            pitcher = {}
            pitcher['role'] = tds[2].text
            pitcher['name'] = tds[5].text
            pitchers.append(pitcher)
    return pitchers

def get_todays_relievers():
    team_pitchers = {}
    for team in team_codes.keys():
        ext = team.lower().replace(' ','-')
        pitchers = get_team_roster(ext)
        team_pitchers[team] = pitchers
    return team_pitchers
