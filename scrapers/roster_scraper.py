import pandas as pd
import json
import os
import time
import datetime
import random
from operator import itemgetter
from scrapers.scraper_utils import get_soup, team_codes

def replace_names(name):
    name = name.replace('C.J. Edwards', 'Carl Edwards Jr.')
    name = name.replace('Seung-Hwan Oh', 'Seung Hwan Oh').replace('Seung hwan Oh', 'Seung Hwan Oh')
    name = name.replace('Dan Winkler', 'Daniel Winkler').replace('Felipe Vazquez','Felipe Rivero')
    name = name.replace('Mike Wright Jr.','Mike Wright').replace('Danny Coulombe', 'Daniel Coulombe')
    name = name.replace('Jorge De La Rosa','Jorge de la Rosa').replace('Felix Peña', 'Felix Pena')
    name = name.replace('Lucas Sims', 'Luke Sims').replace('Mark Leiter Jr.','Mark Leiterx')
    return name

def get_usage_breakdown():
    soup = get_soup('http://dailybaseballdata.com/cgi-bin/bullpen.pl?lookback=7')
    table = soup.find('table', {'cellspacing': 2})
    trs = [tr for tr in table.findAll('tr', {'id': None}) if not tr.has_attr('bgcolor')]
    indices = []
    for ix, tr in enumerate(trs):
        if len(tr.findAll('td')) < 2:
            indices.append(ix)
    indices.append(len(trs))
    team_pitchers = {}
    for ix, index in enumerate(indices[:-1]):
        pitchers = trs[index:indices[ix+1]][:]
        team = pitchers[0].findAll('td')[0].text.replace(u'\xa0', u'').strip().split('   ')[0]
        pitchers = pitchers[1:]
        total_ip = sum([float(tr.findAll('td')[2].text.replace('.1','.33').replace('.2','.67')) for tr in pitchers])
        pitchers_share = {}
        for pitcher in pitchers:
            player = replace_names(pitcher.findAll('td')[0].text.replace(u'\xa0', u'').strip())
            pitchers_share[player] = float(pitcher.findAll('td')[2].text.replace('.1','.33').replace('.2','.67'))/total_ip

        team_pitchers[team] = pitchers_share
    return team_pitchers

def get_current_relievers(team):
    print(team)
    soup = get_soup('https://www.rosterresource.com/mlb-{}'.format(team))
    new_soup = get_soup(soup.find('iframe')['src'].replace('/pubhtml', '/pubhtml/sheet'))
    trs = new_soup.find('tbody').findAll('tr')
    started_bullpen = False
    counter = 0
    pitchers = {}
    last_role = None
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
            if last_role is None or last_role != 'RP':
                last_role = tds[2].text

            if tds[5].text == 'R' or tds[5].text == 'L':
                pitchers[replace_names(tds[4].text)] = last_role
            else:
                pitchers[replace_names(tds[5].text)] = tds[2].text
    return pitchers

def get_todays_relievers():
    team_pitchers = {}
    for team in team_codes.keys():
        team_pitchers[team] = get_current_relievers(team.lower().replace(' ','-'))
    usages = get_usage_breakdown()
    for team, pitchers in team_pitchers.items():
        for pitcher, role in pitchers.items():
            if pitcher not in usages[team] or usages[team][pitcher] == 0:
                print("No usage for", pitcher,"might be a recent callup?")
                team_pitchers[team][pitcher] = (role, 1/(len(usages[team]) + 1))
            else:
                team_pitchers[team][pitcher] = (role, usages[team][pitcher])
        new_sum = sum(n for _,n in team_pitchers[team].values())
        for pitcher, (role, usage) in team_pitchers[team].items():
            team_pitchers[team][pitcher] = (role, usage/new_sum)
        print(team_pitchers[team])
    return team_pitchers
