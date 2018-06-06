import pandas as pd
import json
import os
import time
import datetime
import random
from operator import itemgetter
from scrapers.scraper_utils import get_soup, team_codes, get_days_in_season

def fix_name(name):
    name = name.replace('Matthew Joyce','Matt Joyce').replace('Jackie Bradley', 'Jackie Bradley Jr.')
    name = name.replace('Jacob Faria', 'Jake Faria').replace('Vincent Velasquez', 'Vince Velasquez')
    name = name.replace('J.C. Ramirez', 'JC Ramirez').replace('Nicky Delmonico','Nick Delmonico')
    name = name.replace('Albert Almora', 'Albert Almora Jr.').replace('Jake Junis','Jakob Junis')
    name = name.replace('Philip Gosselin', 'Phil Gosselin').replace('Michael Foltynewicz','Mike Foltynewicz')
    name = name.replace('Mpho\' Ngoepe', 'Gift Ngoepe').replace('Lucas Sims','Luke Sims')
    name = name.replace('Rafael Lopez', 'Raffy Lopez').replace('Dwight Smith Jr.', 'Dwight Smith')
    name = name.replace('Steve Baron', 'Steven Baron').replace('Greg Bird', 'Gregory Bird')
    name = name.replace('Dan Robertson', 'Daniel Robertson')
    return name

def scrape_day_lineups(day):
    print(day)
    time.sleep(random.randint(4,6))
    new_date = datetime.datetime.strptime(day, '%Y-%m-%d').strftime('%m_%d_%Y')

    url = "https://www.fantasylabs.com/api/sportevents/3/"+new_date
    events = json.loads(get_soup(url).find('body').contents[0])

    url = "https://www.fantasylabs.com/api/lineuptracker/3/"+new_date
    players = json.loads(get_soup(url).find('body').contents[0])

    events = sorted(events, key=itemgetter('EventDateTime'))
    lineups = []
    key_acc = []
    for ev in events:
        if ev['EventSummary'] == 'Postponed' or ev['EventSummary'] == 'PPD':
            continue

        lineup_away = dict(date = day,
                           name = ev['VisitorTeam'].replace('St', 'St.'),
                           lineup_status = ev['VisitorLineupStatus'].split()[0])

        lineup_home = dict(date = day,
                           name = ev['HomeTeam'].replace('St', 'St.'),
                           lineup_status = ev['HomeLineupStatus'].split()[0])

        def locate(lineup, player):
            return (str(ev['EventId']) in player['Key'] and
                    lineup['name'] == player['TeamName'].replace('St', 'St.'))

        away_players = list(filter(lambda p: locate(lineup_away, p), players))
        home_players = list(filter(lambda p: locate(lineup_home, p), players))
        if len(away_players) < 10 or len(home_players) < 10:
            print('Bad lineup {} vs {}'.format(lineup_away['name'],lineup_home['name']))

        for player in away_players:
            lineup_away['{}_name'.format(player['LineupOrder'])] = fix_name(player['PlayerName'])
            lineup_away['{}_id'.format(player['LineupOrder'])] = int(player['PlayerId'])
        for player in home_players:
            lineup_home['{}_name'.format(player['LineupOrder'])] = fix_name(player['PlayerName'])
            lineup_home['{}_id'.format(player['LineupOrder'])] = int(player['PlayerId'])

        key = '{}/{}mlb-{}mlb-1'.format(day.replace('-','/'),
                                        team_codes[lineup_away['name']],
                                        team_codes[lineup_home['name']])

        if key in key_acc:
            print("DOUBLE HEADER", key)
            key = key[:-1] + '2'

        lineup_away['key'] = key
        lineup_home['key'] = key
        print(key)
        key_acc.append(key)
        lineups.extend([lineup_away,lineup_home])
    return lineups

def scrape_year_lineups(year=2017):
    season = get_days_in_season(year)
    lineups = []
    for day in season:
        day_lineups = scrape_day_lineups(day)
        lineups.extend(day_lineups)
    return pd.DataFrame(lineups).set_index(['key', 'name'])

if __name__ == '__main__':
    year = 2018
    df = scrape_year_lineups(year=year)
    csv_path = os.path.join('..','data','lineups','lineups_{}.csv'.format(year))
    df.drop_duplicates().to_csv(csv_path)
