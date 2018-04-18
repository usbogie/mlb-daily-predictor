import json
import os
import sqlite3
import pandas as pd
from scrapers.scraper_utils import get_soup, team_codes, get_days_in_season

team_abbrvs = {
  "ARI": "Arizona Diamondbacks",
  "ATL": "Atlanta Braves",
  "BAL": "Baltimore Orioles",
  "BOS": "Boston Red Sox",
  "CHC": "Chicago Cubs",
  "CIN": "Cincinnati Reds",
  "CLE": "Cleveland Indians",
  "COL": "Colorado Rockies",
  "CWS": "Chicago White Sox",
  "DET": "Detroit Tigers",
  "HOU": "Houston Astros",
  "KC": "Kansas City Royals",
  "LAA": "Los Angeles Angels",
  "LAD": "Los Angeles Dodgers",
  "MIA": "Miami Marlins",
  "MIL": "Milwaukee Brewers",
  "MIN": "Minnesota Twins",
  "NYM": "New York Mets",
  "NYY": "New York Yankees",
  "OAK": "Oakland Athletics",
  "PHI": "Philadelphia Phillies",
  "PIT": "Pittsburgh Pirates",
  "SD": "San Diego Padres",
  "SEA": "Seattle Mariners",
  "SF": "San Francisco Giants",
  "STL": "St. Louis Cardinals",
  "TB": "Tampa Bay Rays",
  "TEX": "Texas Rangers",
  "TOR": "Toronto Blue Jays",
  "WSH": "Washington Nationals",
}

#convert american to decimal odds
def c_to_d(odds):
	if '+' in odds:
		return round(float(odds[1:])/100.0 + 1, 2)
	else:
		return round(100.0/float(odds[1:]) + 1, 2)

def get_names(grid):
	teams = grid.find('div', {'class': 'el-div eventLine-team'}).find_all('div', {'class': 'eventLine-value'})
	away = team_abbrvs[teams[0].a.text.split()[0].strip()]
	home = team_abbrvs[teams[1].a.text.split()[0].strip()]
	return (away, home)

def get_money_lines(ml_url, day):
	game_infos = {}
	ml_soup = get_soup(ml_url)
	grids = ml_soup.findAll('div', {'class': 'event-holder holder-complete'})
	grids += ml_soup.findAll('div', {'class': 'event-holder holder-in-progress'})
	grids += ml_soup.findAll('div', {'class': 'event-holder holder-scheduled'})
	key_acc = []
	for grid in grids:
		game_info = {}
		game_info['time'] = grid.find('div',{'class', 'el-div eventLine-time'}).text
		game_info['date'] = day

		try:
			game_info['away'], game_info['home'] = get_names(grid)
		except:
			continue

		lines = grid.findAll('div', {'class': 'el-div eventLine-book'})[2].find_all('div', {'class': 'eventLine-book-value'})
		try:
			game_info['ml_away'] = c_to_d(lines[0].text)
			game_info['ml_home'] = c_to_d(lines[1].text)
		except:
			print('Continuing on',(day,game_info['time'],game_info['away'],game_info['home']))
			continue

		key = day.replace('-','/')+'/'+team_codes[game_info['away']]+'mlb-'+team_codes[game_info['home']]+'mlb-1'
		if key in key_acc:
			print("DOUBLE HEADER", key)
			key = day.replace('-','/')+'/'+team_codes[game_info['away']]+'mlb-'+team_codes[game_info['home']]+'mlb-2'
		game_info['key'] = key
		key_acc.append(key)
		print(key)

		game_infos[(day,game_info['time'],game_info['away'],game_info['home'])] = game_info
	return game_infos

def get_f5_money_lines(ml_url, game_infos, day):
	ml_soup = get_soup(ml_url)
	grids = ml_soup.findAll('div', {'class': 'event-holder holder-complete'})
	grids += ml_soup.findAll('div', {'class': 'event-holder holder-in-progress'})
	grids += ml_soup.findAll('div', {'class': 'event-holder holder-scheduled'})
	for grid in grids:
		time = grid.find('div',{'class', 'el-div eventLine-time'}).text
		away, home = get_names(grid)
		try:
			game_info = game_infos[(day,time,away,home)]
		except:
			continue

		lines = grid.findAll('div', {'class': 'el-div eventLine-book'})[2].find_all('div', {'class': 'eventLine-book-value'})
		try:
			game_info['ml_away_f5'] = c_to_d(lines[0].text)
			game_info['ml_home_f5'] = c_to_d(lines[1].text)
		except:
			pass

def get_run_lines(rl_url, game_infos, day):
	rl_soup = get_soup(rl_url)
	grids = rl_soup.findAll('div', {'class': 'event-holder holder-complete'})
	grids += rl_soup.findAll('div', {'class': 'event-holder holder-in-progress'})
	grids += rl_soup.findAll('div', {'class': 'event-holder holder-scheduled'})
	for grid in grids:
		time = grid.find('div',{'class', 'el-div eventLine-time'}).text
		away, home = get_names(grid)
		try:
			game_info = game_infos[(day,time,away,home)]
		except:
			continue

		lines = grid.findAll('div', {'class': 'el-div eventLine-book'})[2].find_all('div', {'class': 'eventLine-book-value'})
		try:
			game_info['rl_away'] = c_to_d(lines[0].text.split()[1])
			game_info['rl_home'] = c_to_d(lines[1].text.split()[1])
		except:
			pass

def get_f5_run_lines(rl_url, game_infos, day):
	rl_soup = get_soup(rl_url)
	grids = rl_soup.findAll('div', {'class': 'event-holder holder-complete'})
	grids += rl_soup.findAll('div', {'class': 'event-holder holder-in-progress'})
	grids += rl_soup.findAll('div', {'class': 'event-holder holder-scheduled'})
	for grid in grids:
		time = grid.find('div',{'class', 'el-div eventLine-time'}).text
		away, home = get_names(grid)
		try:
			game_info = game_infos[(day,time,away,home)]
		except:
			continue

		lines = grid.findAll('div', {'class': 'el-div eventLine-book'})[2].find_all('div', {'class': 'eventLine-book-value'})
		try:
			game_info['rl_away_f5'] = c_to_d(lines[0].text.split()[1])
			game_info['rl_home_f5'] = c_to_d(lines[1].text.split()[1])
		except:
			pass

def get_totals(total_url, game_infos,day):
	total_soup = get_soup(total_url)
	grids = total_soup.findAll('div', {'class': 'event-holder holder-complete'})
	grids += total_soup.findAll('div', {'class': 'event-holder holder-in-progress'})
	grids += total_soup.findAll('div', {'class': 'event-holder holder-scheduled'})
	for grid in grids:
		time = grid.find('div',{'class', 'el-div eventLine-time'}).text
		away, home = get_names(grid)
		try:
			game_info = game_infos[(day,time,away,home)]
		except:
			continue

		lines = grid.findAll('div', {'class': 'el-div eventLine-book'})[2].find_all('div', {'class': 'eventLine-book-value'})
		try:
			game_info['total_line'] = float(lines[0].text.split()[0].replace("½",".5"))
			game_info['over_odds'] = c_to_d(lines[0].text.split()[1])
			game_info['under_odds'] = c_to_d(lines[1].text.split()[1])
		except:
			pass

def get_f5_totals(total_url, game_infos,day):
	total_soup = get_soup(total_url)
	grids = total_soup.findAll('div', {'class': 'event-holder holder-complete'})
	grids += total_soup.findAll('div', {'class': 'event-holder holder-in-progress'})
	grids += total_soup.findAll('div', {'class': 'event-holder holder-scheduled'})
	for grid in grids:
		time = grid.find('div',{'class', 'el-div eventLine-time'}).text
		away, home = get_names(grid)
		try:
			game_info = game_infos[(day,time,away,home)]
		except:
			continue

		lines = grid.findAll('div', {'class': 'el-div eventLine-book'})[2].find_all('div', {'class': 'eventLine-book-value'})
		try:
			game_info['total_line_f5'] = float(lines[0].text.split()[0].replace("½",".5"))
			game_info['over_odds_f5'] = c_to_d(lines[0].text.split()[1])
			game_info['under_odds_f5'] = c_to_d(lines[1].text.split()[1])
		except:
			pass

def scrape_sbr_day(day):
	print(day)
	base = "https://www.sportsbookreview.com/betting-odds/mlb-baseball/"
	ml_ext = "?date="
	ml_f5_ext = "1st-half/?date="
	rl_ext = "pointspread/?date="
	rl_f5_ext = "pointspread/1st-half/?date="
	total_ext = "totals/?date="
	total_f5_ext = "totals/1st-half/?date="
	ml_url = base + ml_ext + day.replace('-','')
	game_infos = get_money_lines(ml_url, day)
	#handle all star game
	if len(game_infos.keys()) == 0:
		return game_infos
	f5_ml_url = base + ml_f5_ext + day.replace('-','')
	get_f5_money_lines(f5_ml_url, game_infos, day)

	rl_url = base + rl_ext + day.replace('-','')
	get_run_lines(rl_url, game_infos, day)
	rl_f5_url = base + rl_f5_ext + day.replace('-','')
	get_f5_run_lines(rl_f5_url, game_infos, day)

	total_url = base + total_ext + day.replace('-','')
	get_totals(total_url, game_infos, day)
	total_f5_url = base + total_f5_ext + day.replace('-','')
	get_f5_totals(total_f5_url, game_infos, day)
	return game_infos

def scrape_sbr_year(year=2017):
	season_games = []
	season_dates = get_days_in_season(year)

	# ml == money line
	# rl == run line (look it up)
	for day in season_dates:
		game_infos = scrape_sbr_day(day)
		season_games += list(game_infos.values())

	# This is horrible. I hope nobody ever sees this. Maybe need to cross-reference
	# vegas_insider or something. Don't want to put in the work right now
	for game in season_games:
		if 'rl_away' in game:
			continue
		print(game)
		ans = input('entry all fucked up. You want to fill it in? (y/n) -> ')
		if ans == 'n':
			continue
		for key in ['ml_away','ml_home', 'rl_away',\
					'rl_home','total_odds']:
			game[key] = c_to_d(input(key+': '))
		for key in ['total_line']:
			game[key] = float(input(key+': '))
		print(game)

	return pd.DataFrame(season_games).set_index('key')

if __name__ == '__main__':
	year = 2018
	df = scrape_sbr_year(year)
	csv_path = os.path.join('..','data','lines','lines_{}.csv'.format(year))
	df.drop_duplicates().to_csv(csv_path)
