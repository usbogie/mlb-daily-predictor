from datetime import datetime, timedelta, date
import re
import json
import os
import sys
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import urllib.request as request
import urllib.error as error
import sqlite3
import pandas as pd

def get_soup(url):
	ua = UserAgent()
	try:
		page = request.urlopen(request.Request(url, headers = { 'User-Agent' : ua.random }))
	except (ConnectionResetError, error.URLError, error.HTTPError) as e:
		try:
			wait_time = round(max(10, 12 + random.gauss(0,1)), 2)
			time.sleep(wait_time)
			print("First attempt for %s failed. Trying again." % (url))
			page = request.urlopen(request.Request(url, headers = { 'User-Agent' : ua.random }))
		except:
			print(e)
			sys.exit()
	content = page.read()
	return BeautifulSoup(content, "html5lib")

def get_days_in_season(year):
	opening_days = {2017:'2017-04-02'}
	closing_days = {2017:'2017-10-01'}
	months = ['04', '05', '06', '07', '08', '09', '10']
	dates = {'04': list(range(31)[1:]), '05': list(range(32)[1:]), '06': list(range(31)[1:]),
			 '07': list(range(32)[1:]), '08': list(range(32)[1:]), '09': list(range(31)[1:]),
			 '10': list(range(32)[1:])}

	all_season = []
	for month in months:
		for d in dates[month]:
			day = str(d)
			if len(day) == 1:
				day = '0'+day
			date = "{}-{}-{}".format(year,month,day)
			if date < opening_days[year] or date > closing_days[year]:
				continue
			all_season.append(date)

	return all_season

#convert american to decimal odds
def c_to_d(odds):
	if '+' in odds:
		return round(float(odds[1:])/100.0 + 1, 2)
	else:
		return round(100.0/float(odds[1:]) + 1, 2)

def get_money_lines(ml_url, day):
	game_infos = {}
	ml_soup = get_soup(ml_url)
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
	rl_soup = get_soup(rl_url)
	grids = rl_soup.findAll('div', {'class': 'event-holder holder-complete'})
	for grid in grids:
		time = grid.find('div',{'class', 'el-div eventLine-time'}).text
		teams = grid.find('div', {'class': 'el-div eventLine-team'}).find_all('div', {'class': 'eventLine-value'})
		away = teams[0].a.text.split()[0].strip()
		home = teams[1].a.text.split()[0].strip()
		game_info = game_infos[(day,time,away,home)]
		print(away, home)

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
	total_soup = get_soup(total_url)
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

def scrape_sbr(year=2017):
	season_games = []
	season_dates = get_days_in_season(year)
	base = "https://www.sportsbookreview.com/betting-odds/mlb-baseball/"
	ml_ext = "?date="
	rl_ext = "pointspread/?date="
	total_ext = "totals/?date="
	for day in season_dates:
		print(day)
		ml_url = base + ml_ext + day.replace('-','')
		game_infos = get_money_lines(ml_url, day)
		rl_url = base + rl_ext + day.replace('-','')
		get_run_lines(rl_url, game_infos, day)
		total_url = base + total_ext + day.replace('-','')
		get_totals(total_url, game_infos, day)


		season_games += list(game_infos.values())

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
	data = scrape_sbr(year)
	con = sqlite3.connect(os.path.join('data','lines.db3'))
	data.to_sql("lines_{}".format(year), con, if_exists='replace', index=False)
