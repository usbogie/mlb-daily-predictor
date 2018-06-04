from scrapers.scraper_utils import get_soup, team_codes, get_days_in_season
from multiprocessing import Pool
import pandas as pd
import json
import os
import time
import datetime

def parse(game):
    match = {}
    game_url = 'https://statsapi.mlb.com/api/v1.1/game/{}/feed/live?language=en'.format(game['gamePk'])
    soup = json.loads(get_soup(game_url).find('body').contents[0], strict=False)
    match['away'] = soup['liveData']['boxscore']['teams']['away']['team']['name']
    bp_away = soup['liveData']['boxscore']['teams']['away']['bullpen'] + soup['liveData']['boxscore']['teams']['away']['pitchers']
    for ix, arm in enumerate(bp_away):
        match['bp_away_' + str(ix)] = arm
    match['home'] = soup['liveData']['boxscore']['teams']['home']['team']['name']
    bp_home = soup['liveData']['boxscore']['teams']['home']['bullpen'] + soup['liveData']['boxscore']['teams']['home']['pitchers']
    for ix, arm in enumerate(bp_home):
        match['bp_home_' + str(ix)] = arm
    match['key'] = soup['gameData']['game']['id']
    match['date'] = soup['gameData']['datetime']['originalDate']

    return match

def scrape_day_bullpens(day):
    print(day)
    url = 'https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=' + day
    soup = json.loads(get_soup(url).find('body').contents[0], strict=False)
    data = []
    try:
        games = soup['dates'][0]['games']
    except:
        print("continue", day, "all star break or no games")
        return []
    with Pool(10) as p:
        data = p.map(parse, games)
    return data

def scrape_bullpens(year=2017):
    season = get_days_in_season(year)
    lineups = []
    for day in season:
        day_bullpens = scrape_day_bullpens(day)
        lineups.extend(day_bullpens)
    return pd.DataFrame(lineups).set_index(['key'])

if __name__ == '__main__':
    year = 2018
    df = scrape_bullpens(year=year)
    csv_path = os.path.join('..','data','lineups','bullpens_{}.csv'.format(year))
    df.drop_duplicates().to_csv(csv_path)
