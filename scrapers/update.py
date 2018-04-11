from scrapers import mlb_scraper,fantasylabs_lineups, sbr_scraper
from datetime import datetime, timedelta
import pandas as pd
import os

year = 2018
yesterday = (datetime.now() - timedelta(1)).strftime('%Y-%m-%d')
today = datetime.now().strftime('%Y-%m-%d')

def update_games():
    print("getting games")
    mlb_path = os.path.join('data','games','games_{}.csv'.format(year))
    games_df = pd.read_csv(mlb_path)
    yesterday_games = pd.DataFrame(mlb_scraper.get_day_of_games(yesterday))
    updated_games_df = pd.concat([games_df,yesterday_games]).set_index('key')
    updated_games_df.drop_duplicates().to_csv(mlb_path)

def update_lineups():
    print("getting lineups")
    lineups_path = os.path.join('data','lineups','lineups_{}.csv'.format(year))
    lineups_df = pd.read_csv(lineups_path)
    yesterday_lineups = pd.DataFrame(fantasylabs_lineups.scrape_day_lineups(yesterday))
    updated_lineups_df = pd.concat([lineups_df,yesterday_lineups]).set_index('key')
    updated_lineups_df.drop_duplicates().to_csv(lineups_path)

    today_lineups = pd.DataFrame(fantasylabs_lineups.scrape_day_lineups(today)).set_index('key')
    today_lineups.to_csv(os.path.join('data','lineups','today.csv'))

def update_lines():
    print("getting lines")
    lines_path = os.path.join('data','lines','lines_{}.csv'.format(year))
    lines_df = pd.read_csv(lines_path)
    yesterday_lines = pd.DataFrame(list(sbr_scraper.scrape_sbr_day(yesterday).values()))
    updated_lines_df = pd.concat([lines_df,yesterday_lines]).set_index('key')
    updated_lines_df.drop_duplicates().to_csv(lines_path)

    today_lines = pd.DataFrame(list(sbr_scraper.scrape_sbr_day(today).values())).set_index('key')
    today_lines.to_csv(os.path.join('data','lines','today.csv'))

def update_all():
    update_games()
    update_lineups()
    update_lines()

update_all()
