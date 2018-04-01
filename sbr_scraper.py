import json
import os
import sqlite3
import pandas as pd
import scraper_utils

#convert american to decimal odds
def c_to_d(odds):
	if '+' in odds:
		return round(float(odds[1:])/100.0 + 1, 2)
	else:
		return round(100.0/float(odds[1:]) + 1, 2)

def get_money_lines(ml_url, day):
	game_infos = {}
	ml_soup = scraper_utils.get_soup(ml_url)
	grids = ml_soup.findAll('div', {'class': 'event-holder holder-complete'})
	for grid in grids:
		game_info = {}
		game_info['time'] = grid.find('div',{'class', 'el-div eventLine-time'}).text
		game_info['date'] = day

		teams = grid.find('div', {'class': 'el-div eventLine-team'}).find_all('div', {'class': 'eventLine-value'})
		game_info['away'] = teams[0].a.text.split()[0].strip()
		game_info['home'] = teams[1].a.text.split()[0].strip()

		open_lines = grid.find('div', {'class': 'el-div eventLine-opener'}).find_all('div', {'class': 'eventLine-book-value'})
		try:
			game_info['ml_away_open'] = c_to_d(open_lines[0].text)
			game_info['ml_home_open'] = c_to_d(open_lines[1].text)
		except:
			game_infos[(day,game_info['time'],game_info['away'],game_info['home'])] = game_info
			continue

		close_lines = grid.findAll('div', {'class': 'el-div eventLine-book'})[1].find_all('div', {'class': 'eventLine-book-value'})
		try:
			game_info['ml_away_close'] = c_to_d(close_lines[0].text)
			game_info['ml_home_close'] = c_to_d(close_lines[1].text)
		except:
			continue

		game_infos[(day,game_info['time'],game_info['away'],game_info['home'])] = game_info
	return game_infos

def get_run_lines(rl_url, game_infos, day):
	rl_soup = scraper_utils.get_soup(rl_url)
	grids = rl_soup.findAll('div', {'class': 'event-holder holder-complete'})
	for grid in grids:
		time = grid.find('div',{'class', 'el-div eventLine-time'}).text
		teams = grid.find('div', {'class': 'el-div eventLine-team'}).find_all('div', {'class': 'eventLine-value'})
		away = teams[0].a.text.split()[0].strip()
		home = teams[1].a.text.split()[0].strip()
		game_info = game_infos[(day,time,away,home)]
		print(away, '@', home)

		open_lines = grid.find('div', {'class': 'el-div eventLine-opener'}).find_all('div', {'class': 'eventLine-book-value'})
		try:
			game_info['rl_away_open'] = c_to_d(open_lines[0].text.split()[1])
			game_info['rl_home_open'] = c_to_d(open_lines[1].text.split()[1])
		except:
			pass

		close_lines = grid.findAll('div', {'class': 'el-div eventLine-book'})[1].find_all('div', {'class': 'eventLine-book-value'})
		try:
			game_info['rl_away_close'] = c_to_d(close_lines[0].text.split()[1])
			game_info['rl_home_close'] = c_to_d(close_lines[1].text.split()[1])
		except:
			pass

def get_totals(total_url, game_infos,day):
	total_soup = scraper_utils.get_soup(total_url)
	grids = total_soup.findAll('div', {'class': 'event-holder holder-complete'})
	for grid in grids:
		time = grid.find('div',{'class', 'el-div eventLine-time'}).text
		teams = grid.find('div', {'class': 'el-div eventLine-team'}).find_all('div', {'class': 'eventLine-value'})
		away = teams[0].a.text.split()[0].strip()
		home = teams[1].a.text.split()[0].strip()
		game_info = game_infos[(day,time,away,home)]

		open_totals = grid.find('div', {'class': 'el-div eventLine-opener'}).find_all('div', {'class': 'eventLine-book-value'})
		try:
			game_info['total_open_line'] = float(open_totals[0].text.split()[0].replace("½",".5"))
			game_info['total_open_odds'] = c_to_d(open_totals[0].text.split()[1])
		except:
			pass

		close_lines = grid.findAll('div', {'class': 'el-div eventLine-book'})[1].find_all('div', {'class': 'eventLine-book-value'})
		try:
			game_info['total_close_line'] = float(close_lines[0].text.split()[0].replace("½",".5"))
			game_info['total_close_odds'] = c_to_d(close_lines[0].text.split()[1])
		except:
			pass

def scrape_sbr_day(day):
	print(day)
	base = "https://www.sportsbookreview.com/betting-odds/mlb-baseball/"
	ml_ext = "?date="
	rl_ext = "pointspread/?date="
	total_ext = "totals/?date="
	ml_url = base + ml_ext + day.replace('-','')
	game_infos = get_money_lines(ml_url, day)
	rl_url = base + rl_ext + day.replace('-','')
	get_run_lines(rl_url, game_infos, day)
	total_url = base + total_ext + day.replace('-','')
	get_totals(total_url, game_infos, day)
	return game_infos

def scrape_sbr_year(year=2017):
	season_games = []
	season_dates = scraper_utils.get_days_in_season(year)

	# ml == money line
	# rl == run line (look it up)
	for day in season_dates:
		game_infos = scrape_sbr_day(day)
		season_games += list(game_infos.values())

	# This is horrible. I hope nobody ever sees this. Maybe need to cross-reference
	# vegas_insider or something. Don't want to put in the work right now
	for game in season_games:
		if 'rl_away_open' in game:
			continue
		print(game)
		ans = input('entry all fucked up. You want to fill it in? (y/n) -> ')
		if ans == 'n':
			continue
		for key in ['ml_away_open','ml_home_open','ml_away_close','ml_home_close','rl_away_open','rl_home_open',\
				'rl_away_close','rl_home_close','total_open_odds','total_close_odds']:
			game[key] = c_to_d(input(key+': '))
		for key in ['total_open_line','total_close_line']:
			game[key] = float(input(key+': '))
		print(game)

	return pd.DataFrame(season_games)

if __name__ == '__main__':
	year = 2017
	data = scrape_sbr_year(year)
	con = sqlite3.connect(os.path.join('data','lines.db3'))
	data.to_sql("lines_{}".format(year), con, if_exists='replace', index=False)
