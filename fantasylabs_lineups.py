from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import urllib.request as request
import urllib.error as error
import pandas as pd
import sys
import json
import os
import datetime

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


    #LiveBoard1_LiveBoard1_litGamesPanel
def scrape_lineups(date):
    url = "https://www.fantasylabs.com/api/lineuptracker/3/"+date
    soup = json.loads(get_soup(url).find('body').contents[0])
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
