from scrapers import bullpen_scraper, mlb_scraper, fantasylabs_lineups, sbr_scraper, roster_scraper
from datetime import datetime, timedelta
import pandas as pd
import os

year = 2018
yesterday = (datetime.now() - timedelta(1)).strftime('%Y-%m-%d')
today = (datetime.now() + timedelta(0)).strftime('%Y-%m-%d')

def get_dates(df):
    last_scraped = max(df['date'].tolist())
    if last_scraped == yesterday:
        return [yesterday]
    start = datetime.strptime(last_scraped, '%Y-%m-%d')
    end = datetime.strptime(yesterday, '%Y-%m-%d')
    delta = end - start

    days = []
    for i in range(delta.days + 1):
        days.append((start + timedelta(i)).strftime('%Y-%m-%d'))
    return days

def update_games():
    print("getting games")
    mlb_path = os.path.join('data','games','games_{}.csv'.format(year))
    games_df = pd.read_csv(mlb_path)
    days = get_dates(games_df)
    games = []
    for day in days:
        games.extend(mlb_scraper.get_day_of_games(yesterday))
    past_games = pd.DataFrame(games)
    updated_games_df = pd.concat([games_df,past_games]).set_index('key')
    updated_games_df.drop_duplicates().to_csv(mlb_path)

def update_bullpens():
    print("getting bullpens")
    bullpens_path = os.path.join('data','lineups','bullpens_{}.csv'.format(year))
    bullpens_df = pd.read_csv(bullpens_path)
    days = get_dates(bullpens_df)
    bullpens = []
    for day in days:
        bullpens.extend(bullpen_scraper.scrape_day_bullpens(day))
    past_bullpens = pd.DataFrame(bullpens)
    updated_bullpens_df = pd.concat([bullpens_df,past_bullpens]).set_index('key')
    updated_bullpens_df.drop_duplicates().to_csv(bullpens_path)

def update_lineups():
    print("getting lineups")
    lineups_path = os.path.join('data','lineups','lineups_{}.csv'.format(year))
    lineups_df = pd.read_csv(lineups_path)
    days = get_dates(lineups_df)
    lineups = []
    for day in days:
        lineups.extend(fantasylabs_lineups.scrape_day_lineups(day))
    past_lineups = pd.DataFrame(lineups)
    updated_lineups_df = pd.concat([lineups_df,past_lineups]).set_index('key')
    updated_lineups_df.drop_duplicates().to_csv(lineups_path)

    today_lineups = pd.DataFrame(fantasylabs_lineups.scrape_day_lineups(today)).set_index('key')
    today_lineups.to_csv(os.path.join('data','lineups','today.csv'))

def update_lines():
    print("getting lines")
    lines_path = os.path.join('data','lines','lines_{}.csv'.format(year))
    lines_df = pd.read_csv(lines_path)
    days = get_dates(lines_df)
    lines = []
    for day in days:
        lines.extend(list(sbr_scraper.scrape_sbr_day(day).values()))
    past_lines = pd.DataFrame(lines)
    updated_lines_df = pd.concat([lines_df,past_lines]).set_index('key')
    updated_lines_df.drop_duplicates().to_csv(lines_path)

    today_lines = pd.DataFrame(list(sbr_scraper.scrape_sbr_day(today).values())).set_index('key')
    today_lines.to_csv(os.path.join('data','lines','today.csv'))

def get_relievers():
    pitchers = roster_scraper.get_todays_relievers()
    import json
    with open(os.path.join('data','relievers.json'), 'w') as outfile:
        json.dump(pitchers, outfile)
    print("RELIEVERS SAVED\n\n")

def update_all(gr):
    if (gr):
        get_relievers()
    update_games()
    update_bullpens()
    update_lineups()
    update_lines()
