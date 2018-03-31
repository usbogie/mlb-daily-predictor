from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import urllib.request as request
import urllib.error as error
import pandas as pd
import sys
import json
import os

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

def get_teams(year):
	teams_url = "http://lookup-service-prod.mlb.com/json/named.team_all_season.bam?all_star_sw=%27N%27&sport_code=%27mlb%27&sort_order=%27name_asc%27&season=" + str(year)
	soup = json.loads(get_soup(teams_url).find('body').contents[0], strict=False)
	all_teams = soup['team_all_season']['queryResults']['row']
	team_list = []
	for team in all_teams:
		team_obj = {}
		team_obj['city'] = team['name_short']
		team_obj['name'] = team['name']
		team_obj['code'] = team['team_code']
		team_obj['id'] = team['team_id']
		team_obj['league'] = team['league_abbrev']
		team_obj['venue_id'] = team['venue_id']
		team_obj['venue_name'] = team['venue_short']
		team_list.append(team_obj)

	return team_list

def get_pitcher_logs(year, player_id):
	player_log_url = "http://lookup-service-prod.mlb.com/json/" + \
		"named.sport_pitching_game_log_composed.bam?game_type=%27R%27" + \
		"&league_list_id=%27mlb_hist%27&player_id="+player_id+"&season="+str(year)
	soup = json.loads(get_soup(player_log_url).find('body').contents[0], strict=False)
	pitcher_logs = soup['sport_pitching_game_log_composed']['sport_pitching_game_log']['queryResults']['row']
	ex_keys = ['game_type','game_nbr','game_day','opponent','opponent_short',
			   'sport_id','sport','avg','opp_score','team_score','game_date',
			   'team','obp','np','team_result','whip','tbf','cg','gs','irs',
			   'era','g','w','l','s','sho','sv','ir','go_ao']
	saved_logs = []
	for log in pitcher_logs:
		new_log = {}
		for key, val in log.items():
			if key not in ex_keys:
				new_log[key] = val
		saved_logs.append(new_log)
	return pd.DataFrame(saved_logs)

def get_batter_logs(year, player_id):
	player_log_url = "http://lookup-service-prod.mlb.com/json/" + \
		"named.sport_hitting_game_log_composed.bam?game_type=%27R%27" + \
		"&league_list_id=%27mlb_hist%27&player_id="+player_id+"&season="+str(year)
	soup = json.loads(get_soup(player_log_url).find('body').contents[0], strict=False)
	batter_logs = soup['sport_hitting_game_log_composed']['sport_hitting_game_log']['queryResults']['row']
	ex_keys = ['game_type','game_nbr','lob','game_day','opponent',
			   'opponent_short','sport_id','slg','avg','opp_score','go_ao',
			   'team_score','ops','game_date','sport','team','obp','team_result']
	saved_logs = []
	for log in batter_logs:
		new_log = {}
		for key, val in log.items():
			if key not in ex_keys:
				new_log[key] = val
		saved_logs.append(new_log)
	return pd.DataFrame(saved_logs)

def get_team_logs(year, team_id):
	url = "http://mlb.mlb.com/pubajax/wf/flow/stats.splayer?season="+str(year)+ \
		"&stat_type=hitting&page_type=SortablePlayer&team_id="+str(team_id)+ \
		"&game_type=%27R%27&player_pool=ALL&season_type=ANY&sport_code=%27mlb%27&results=1000&recSP=1&recPP=50"
	soup = json.loads(get_soup(url).find('body').contents[0], strict=False)
	players = soup['stats_sortable_player']['queryResults']['row']
	team_pitcher_logs = []
	team_batter_logs = []
	for player in players:
		if player['pos'] == 'P':
			try:
				pitcher_logs = get_pitcher_logs(year, player['player_id'])
			except:
				print("Something wrong with", player['name_display_first_last'])
				if input("skip? (y/n) ") == 'n':
					sys.exit()
				else:
					continue
			print(player['name_display_first_last'], "is a pitcher and had", len(pitcher_logs), "appearances in 2017")
			team_pitcher_logs.append(pitcher_logs)
		else:
			if player['tpa'] == 0:
				print(player['name_display_first_last'], "has no plate appearances")
				continue

			batter_logs = get_batter_logs(year, player['player_id'])
			print(player['name_display_first_last'], "is a batter and had", len(batter_logs), "appearances in 2017")
			team_batter_logs.append(batter_logs)

	return (pd.DataFrame(team_pitcher_logs), pd.DataFrame(team_batter_logs))


def scrape_player_stats(year=2017):
	teams = get_teams(year)
	for team in teams:
		print(team['name'])
		pitchers, batters = get_team_logs(year,team['id'])
		#TODO figure out best DB storage method


if __name__ == '__main__':
	year = 2017
	scrape_player_stats(year=year)
