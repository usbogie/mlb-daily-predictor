from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import urllib.request as request
import urllib.error as error
import pandas as pd
import sys
import json
import os

names = {
  "Boston": "BOS",
  "N.Y. Yankees": "NYY",
  "Arizona": "ARI",
  "Atlanta": "ATL",
  "Baltimore": "BAL",
  "Chi. Cubs": "CHC",
  "Chi. White Sox": "CHW",
  "Cincinnati": "CIN",
  "Cleveland": "CLE",
  "Colorado": "COL",
  "Detroit": "DET",
  "Miami": "FLA",
  "Houston": "HOU",
  "Kansas City": "KCR",
  "L.A. Angels": "ANA",
  "L.A. Dodgers": "LAD",
  "Milwaukee": "MIL",
  "Minnesota": "MIN",
  "N.Y. Mets": "NYM",
  "Oakland": "OAK",
  "Philadelphia": "PHI",
  "Pittsburgh": "PIT",
  "San Diego": "SDP",
  "San Francisco": "SFG",
  "Seattle": "SEA",
  "St. Louis": "STL",
  "Tampa Bay": "TBD",
  "Texas": "TEX",
  "Toronto": "TOR",
  "Washington": "WSN"
}

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

def scrape_player_stats(year=2017):
    teams_url = 'https://www.baseball-reference.com/teams/'
    for abbrv in names.values():
        soup = get_soup(teams_url+abbrv+'/'+str(year)+'.shtml')
        batters = soup.find('table', {'id':'team_batting'})
        pitchers = soup.find('table', {'id':'team_pitching'})
        batter_links = [link['href'] for link in searchable1.findAll('a') if '/players' in link['href']]
        pitcher_links = [link['href'] for link in searchable2.findAll('a') if '/players' in link['href']]
        



if __name__ == '__main__':
	year = 2017
	cur_season = scrape_player_stats(year=year)
	cur_season.to_csv(csv_path, index=False)
	print("Updated cbbref")
