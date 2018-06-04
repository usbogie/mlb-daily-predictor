import pandas as pd
import sys
import json
import os
import time
from scrapers.scraper_utils import team_codes, get_soup, get_days_in_season

def get_day_of_games(day):
	url = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&date="+day+"&hydrate=linescore(matchup,runners)"
	soup = json.loads(get_soup(url).find('body').contents[0], strict=False)
	try:
		games = soup['dates'][0]['games']
	except:
		print("continue", day, "all star break or no games")
		return []
	key_acc = []
	todays_games = []
	for game in games:
		game_obj = {}
		if game['status']['detailedState'] == 'Postponed' or game['status']['detailedState'] == 'Suspended':
			continue
		if 'All-Stars' in game['teams']['away']['team']['name']:
			print("all star game, continue")
			continue
		game_obj['gamePk'] = game['gamePk']
		game_obj['date'] = day
		game_obj['away_id'] = game['teams']['away']['team']['id']
		game_obj['away'] = game['teams']['away']['team']['name']
		game_obj['away_score'] = game['teams']['away']['score']
		game_obj['home_id'] = game['teams']['home']['team']['id']
		game_obj['home'] = game['teams']['home']['team']['name']
		game_obj['home_score'] = game['teams']['home']['score']
		key = day.replace('-','/')+'/'+team_codes[game_obj['away']]+'mlb-'+team_codes[game_obj['home']]+'mlb-1'
		if key in key_acc:
			print("DOUBLE HEADER", key)
			key = day.replace('-','/')+'/'+team_codes[game_obj['away']]+'mlb-'+team_codes[game_obj['home']]+'mlb-2'
		game_obj['key'] = key
		print(key)
		key_acc.append(key)
		todays_games.append(game_obj)
	return todays_games

def scrape_games(year=2017):
	season_days = get_days_in_season(year)
	season_games = []
	for day in season_days:
		todays_games = get_day_of_games(day)
		season_games += todays_games
		time.sleep(1)
	season_df = pd.DataFrame(season_games).set_index('key')
	print(season_df)
	return season_df

if __name__ == '__main__':
	year = 2018
	df = scrape_games(year=year)
	csv_path = os.path.join('..','data','games','games_{}.csv'.format(year))
	df.drop_duplicates().to_csv(csv_path)
