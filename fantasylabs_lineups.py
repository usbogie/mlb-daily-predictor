import pandas as pd
import json
import os
import datetime
import scraper_utils

def scrape_lineups(date):
    url = "https://www.fantasylabs.com/api/lineuptracker/3/"+date
    soup = json.loads(scraper_utils.get_soup(url).find('body').contents[0])
    import collections
    dol = collections.defaultdict(list)
    for d in soup:
        k = d["TeamName"]
        dol[k].append(d)

    teams = dict(dol)
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
        lineups[team]=team_lineup

    return lineups

if __name__ == '__main__':
    date = datetime.datetime.now().strftime("%m_%d_%Y")
    lineups = scrape_lineups(date)
    with open('data/todays_lineups.json', 'w') as outfile:
        json.dump(lineups, outfile, sort_keys = True, indent = 4, ensure_ascii = False)
