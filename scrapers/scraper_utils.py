from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, date
from random import random, gauss
import time
import sys
import requests
import urllib.request as request
import urllib.error as error

team_codes = {
	"Arizona Diamondbacks": "ari",
	"Atlanta Braves": "atl",
	"Baltimore Orioles": "bal",
	"Boston Red Sox": "bos",
	"Chicago Cubs": "chn",
	"Chicago White Sox": "cha",
	"Cincinnati Reds": "cin",
	"Cleveland Indians": "cle",
	"Colorado Rockies": "col",
	"Detroit Tigers": "det",
	"Houston Astros": "hou",
	"Kansas City Royals": "kca",
	"Los Angeles Angels": "ana",
	"Los Angeles Dodgers": "lan",
	"Miami Marlins": "mia",
	"Milwaukee Brewers": "mil",
	"Minnesota Twins": "min",
	"New York Mets": "nyn",
	"New York Yankees": "nya",
	"Oakland Athletics": "oak",
	"Philadelphia Phillies": "phi",
	"Pittsburgh Pirates": "pit",
	"San Diego Padres": "sdn",
	"San Francisco Giants": "sfn",
	"Seattle Mariners": "sea",
	"St. Louis Cardinals": "sln",
	"Tampa Bay Rays": "tba",
	"Texas Rangers": "tex",
	"Toronto Blue Jays": "tor",
	"Washington Nationals": "was",
}

team_leagues = {
	"ari": "NL",
	"atl": "NL",
	"bal": "AL",
	"bos": "AL",
	"chn": "NL",
	"cha": "AL",
	"cin": "NL",
	"cle": "AL",
	"col": "NL",
	"det": "AL",
	"hou": "AL",
	"kcr": "AL",
	"ana": "AL",
	"lan": "NL",
	"mia": "NL",
	"mil": "NL",
	"min": "AL",
	"nyn": "NL",
	"nya": "AL",
	"oak": "AL",
	"phi": "NL",
	"pit": "NL",
	"sdn": "NL",
	"sfn": "NL",
	"sea": "AL",
	"sln": "NL",
	"tba": "AL",
	"tex": "AL",
	"tor": "AL",
	"was": "NL",
}

alt_team_codes = {
	"Diamondbacks": "ari",
	"Braves": "atl",
	"Orioles": "bal",
	"Red Sox": "bos",
	"Cubs": "chn",
	"White Sox": "cha",
	"Reds": "cin",
	"Indians": "cle",
	"Rockies": "col",
	"Tigers": "det",
	"Astros": "hou",
	"Royals": "kca",
	"Angels": "ana",
	"Dodgers": "lan",
	"Marlins": "mia",
	"Brewers": "mil",
	"Twins": "min",
	"Mets": "nyn",
	"Yankees": "nya",
	"Athletics": "oak",
	"Phillies": "phi",
	"Pirates": "pit",
	"Padres": "sdn",
	"Giants": "sfn",
	"Mariners": "sea",
	"Cardinals": "sln",
	"Rays": "tba",
	"Rangers": "tex",
	"Blue Jays": "tor",
	"Nationals": "was",
}

fangraphs_to_mlb = {
	"ARI": "ari",
	"ATL": "atl",
	"BAL": "bal",
	"BOS": "bos",
	"CHC": "chn",
	"CHW": "cha",
	"CIN": "cin",
	"CLE": "cle",
	"COL": "col",
	"DET": "det",
	"HOU": "hou",
	"KCR": "kca",
	"LAA": "ana",
	"LAD": "lan",
	"MIA": "mia",
	"FLA": "mia",
	"MIL": "mil",
	"MIN": "min",
	"NYM": "nyn",
	"NYY": "nya",
	"OAK": "oak",
	"PHI": "phi",
	"PIT": "pit",
	"SDP": "sdn",
	"SFG": "sfn",
	"SEA": "sea",
	"STL": "sln",
	"TBR": "tba",
	"TEX": "tex",
	"TOR": "tor",
	"WSN": "was",
}

def get_soup(url, check_500 = False):
	ua = UserAgent()
	try:
		if check_500:
			try:
				resp = requests.head(url)
			except:
				time.sleep(30)
				resp = requests.head(url)
			if str(resp) == "<Response [500]>":
				print("500 for url", url)
				return None
		page = request.urlopen(request.Request(url, headers = { 'User-Agent' : ua.random }))
	except (ConnectionResetError, error.URLError, error.HTTPError) as e:
		print(e)
		wait_time = round(max(60, 12 + gauss(0,1)), 2)
		print("First attempt for %s failed. Trying again." % (url))
		time.sleep(wait_time)
		page = request.urlopen(request.Request(url, headers = { 'User-Agent' : ua.random }))
	content = page.read()
	return BeautifulSoup(content, "html5lib")

def get_days_in_season(year):
	opening_days = {2017:'2017-04-02',2018:'2018-03-29'}
	closing_days = {2017:'2017-10-01',2018:'2018-10-31'}
	months = ['03','04', '05', '06', '07', '08', '09', '10']
	dates = {'03': list(range(32)[1:]), '04': list(range(31)[1:]), '05': list(range(32)[1:]),
			 '06': list(range(31)[1:]), '07': list(range(32)[1:]), '08': list(range(32)[1:]),
			 '09': list(range(31)[1:]), '10': list(range(32)[1:])}

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
