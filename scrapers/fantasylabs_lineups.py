import pandas as pd
import json
import os
import sys
import time
import datetime
import random
from scrapers.scraper_utils import get_soup, team_codes, get_days_in_season

def fix_name(name):
    name = name.replace('Matthew Joyce','Matt Joyce').replace('Jackie Bradley', 'Jackie Bradley Jr.')
    name = name.replace('Jacob Faria', 'Jake Faria').replace('Vincent Velasquez', 'Vince Velasquez')
    name = name.replace('J.C. Ramirez', 'JC Ramirez').replace('Nicky Delmonico','Nick Delmonico')
    name = name.replace('Albert Almora', 'Albert Almora Jr.').replace('Jake Junis','Jakob Junis')
    name = name.replace('Philip Gosselin', 'Phil Gosselin').replace('Michael Foltynewicz','Mike Foltynewicz')
    name = name.replace('Mpho\' Ngoepe', 'Gift Ngoepe').replace('Lucas Sims','Luke Sims')
    return name

def scrape_day_lineups(day):
    time.sleep(random.randint(4,6))
    new_date = datetime.datetime.strptime(day, '%Y-%m-%d').strftime('%m_%d_%Y')
    url = "https://www.fantasylabs.com/api/lineuptracker/3/"+new_date
    soup = json.loads(get_soup(url).find('body').contents[0])

    lineups = []
    something_messed_up = False
    while len(soup) > 0:
        team1 = dict(date = day)
        team2 = dict(date = day)
        if soup[0]['TeamName'] != soup[9]['TeamName']:
            print("not enough entries for", soup[0]['TeamName'])
            missing_player, spot = input("Enter missing player and lineup spot -> ").split(', ')
            soup.insert(int(spot)-1,dict(PlayerName = missing_player))
            something_messed_up = True
        if len(soup) < 20 or soup[10]['TeamName'] != soup[19]['TeamName']:
            print(soup)
            print("not enough entries for", soup[10]['TeamName'])
            missing_player, spot = input("Enter missing player and lineup spot -> ").split(', ')
            soup.insert(10+int(spot)-1,dict(PlayerName = missing_player))
            something_messed_up = True
        team1_lineup = soup[:10]
        team2_lineup = soup[10:20]
        team1['name'] = team1_lineup[0]['TeamName'].replace('St', 'St.')
        team2['name'] = team2_lineup[0]['TeamName'].replace('St', 'St.')
        for i in range(10):
            team1[str(i+1)] = fix_name(team1_lineup[i]['PlayerName'])
            team2[str(i+1)] = fix_name(team2_lineup[i]['PlayerName'])
        soup = soup[20:]
        lineups.append((team1,team2))

    time.sleep(random.randint(1,3))
    url = "https://www.fantasylabs.com/api/sportevents/3/"+new_date
    events = json.loads(get_soup(url).find('body').contents[0])
    for event in events:
        event['used'] = False
    key_acc = []
    day_lineups = []
    for team1, team2 in lineups:
        event = {}
        home = away = None
        for item in events:
            if item['used']:
                continue
            if item['HomeTeam'].replace('St', 'St.') == team1['name'] and \
                    item['VisitorTeam'].replace('St', 'St.') == team2['name']:
                home = team1
                away = team2
                item['used'] = True
                event = item
                break
            elif item['HomeTeam'].replace('St', 'St.') == team2['name'] and \
                    item['VisitorTeam'].replace('St', 'St.') == team1['name']:
                away = team1
                home = team2
                item['used'] = True
                event = item
                break

        if event['EventSummary'] == 'Postponed' or event['EventSummary'] == 'PPD':
            continue

        home['lineup_status'] = event['HomeLineupStatus'].split()[0]
        away['lineup_status'] = event['VisitorLineupStatus'].split()[0]

        key = day.replace('-','/')+'/'+team_codes[away['name']]+'mlb-'+team_codes[home['name']]+'mlb-1'
        if key in key_acc:
            print("DOUBLE HEADER", key)
            key = day.replace('-','/')+'/'+team_codes[away['name']]+'mlb-'+team_codes[home['name']]+'mlb-2'
        home['key'] = key
        away['key'] = key
        print(key)
        key_acc.append(key)
        if something_messed_up:
            print(away)
            print(home)
        day_lineups.extend([away,home])
    return day_lineups

def scrape_year_lineups(year=2017):
    season = get_days_in_season(year)
    lineups = []
    for day in season:
        lineups.extend(scrape_day_lineups(day))
    return pd.DataFrame(lineups).set_index(['key', 'name'])

if __name__ == '__main__':
    year = 2018
    df = scrape_year_lineups(year=year)
    csv_path = os.path.join('..','data','lineups','lineups_{}.csv'.format(year))
    df.drop_duplicates().to_csv(csv_path)
