import pandas as pd
import json
import os
import datetime
import collections
from scraper_utils import get_soup, team_codes

def scrape_todays_lineups(date):
    url = "https://www.fantasylabs.com/api/lineuptracker/3/"+date
    soup = json.loads(get_soup(url).find('body').contents[0])

    # some defaultdict magic to group players by Team Name
    dol = collections.defaultdict(list)
    for d in soup:
        k = d["TeamName"]
        dol[k].append(d)

    # convert defaultdict to regular dic
    teams = dict(dol)

    # pull out the important stuff
    lineups = {}
    for team, lineup in teams.items():
        team_lineup = []
        for player in lineup:
            player_obj = {}
            player_obj['id'] = player['PlayerId']
            player_obj['name'] = player['PlayerName']
            player_obj['slot'] = player['LineupOrder']
            player_obj['position'] = player['Position']
            team_lineup.append(player_obj)
        team = team.replace('St','St.')
        lineups[team]=team_lineup

    # now get all games, pull up important stuff, create keys to match with mlb scores/game logs
    url = "https://www.fantasylabs.com/api/sportevents/3/"+date
    soup = json.loads(get_soup(url).find('body').contents[0])
    games = []
    key_acc = []
    # change date format from fantasylabs requirements to general requirement
    new_date = datetime.datetime.strptime(date, '%m_%d_%Y').strftime('%Y-%m-%d')
    for game in soup:
        game_obj = {}
        if game['EventSummary'] == 'Postponed':
            continue
        game_obj['home'] = game['HomeTeam'].replace('St', 'St.')
        game_obj['away'] = game['VisitorTeam'].replace('St', 'St.')
        game_obj['date'] = new_date
        game_obj['home_lineup_status'] = game['HomeLineupStatus']
        game_obj['away_lineup_status'] = game['VisitorLineupStatus']

        # handle the case of duplicated IDs with double headers
        # triple headers are banned by the current CBA and need not be handled
        key = new_date+'/'+team_codes[game_obj['away']]+'mlb-'+team_codes[game_obj['home']]+'mlb-1'
        if key in key_acc:
            print("DOUBLE HEADER", key)
            key = new_date+'/'+team_codes[game_obj['away']]+'mlb-'+team_codes[game_obj['home']]+'mlb-2'
        game_obj['key'] = key
        key_acc.append(key)
        games.append(game_obj)
        print(game_obj)

    #return lineups

if __name__ == '__main__':
    date = datetime.datetime.now().strftime("%m_%d_%Y")
    lineups = scrape_todays_lineups(date)
    # with open('data/todays_lineups.json', 'w') as outfile:
    #     json.dump(lineups, outfile, sort_keys = True, indent = 4, ensure_ascii = False)
