import pandas as pd
import sys
import json
import os
import time
from scraper_utils import team_codes, get_soup, get_days_in_season

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
			   'sport_id','sport','avg','opp_score','team_score',
			   'team','obp','np','team_result','whip','cg','irs',
			   'era','g','w','l','s','sho','sv','ir','go_ao']
	#pitchers with one outing have a single dict of logs, instead of a list
	if type(pitcher_logs) is dict:
		pitcher_logs = [pitcher_logs]

	saved_logs = []
	for log in pitcher_logs:
		new_log = {}
		for key, val in log.items():
			if key not in ex_keys:
				if key == 'game_date':
					val = val.split('T')[0]
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
			   'team_score','ops','sport','team','obp','team_result']
	#pitchers with one outing have a single dict of logs, instead of a list
	if type(batter_logs) is dict:
		batter_logs = [batter_logs]
	saved_logs = []
	for log in batter_logs:
		new_log = {}
		for key, val in log.items():
			if key not in ex_keys:
				if key == 'game_date':
					val = val.split('T')[0]
				new_log[key] = val
		saved_logs.append(new_log)
	return pd.DataFrame(saved_logs)

def get_team_logs(year, team_id):
	url = "http://mlb.mlb.com/pubajax/wf/flow/stats.splayer?season="+str(year)+ \
		"&stat_type=hitting&page_type=SortablePlayer&team_id="+str(team_id)+ \
		"&game_type=%27R%27&player_pool=ALL&season_type=ANY&sport_code=%27mlb%27&results=1000&recSP=1&recPP=50"
	soup = json.loads(get_soup(url).find('body').contents[0], strict=False)
	hitters = [p for p in soup['stats_sortable_player']['queryResults']['row'] if p['pos'] != 'P']
	url = "http://mlb.mlb.com/pubajax/wf/flow/stats.splayer?season="+str(year)+ \
		"&stat_type=pitching&page_type=SortablePlayer&team_id="+str(team_id)+ \
		"&game_type=%27R%27&player_pool=ALL&season_type=ANY&sport_code=%27mlb%27&results=1000&recSP=1&recPP=50"
	soup = json.loads(get_soup(url).find('body').contents[0], strict=False)
	pitchers = soup['stats_sortable_player']['queryResults']['row']
	team_pitcher_logs = []
	team_batter_logs = []
	for pitcher in pitchers:
		try:
			pitcher_logs = get_pitcher_logs(year, pitcher['player_id'])
		except:
			print("Something wrong with", pitcher['name_display_first_last'])
			continue
		print(pitcher['name_display_first_last'], "is a pitcher and had", len(pitcher_logs), "appearances in", year)
		team_pitcher_logs.append(pitcher_logs)

	for hitter in hitters:
		if hitter['tpa'] == 0:
			print(hitter['name_display_first_last'], "has no plate appearances")
			continue

		try:
			batter_logs = get_batter_logs(year, hitter['player_id'])
		except:
			print("Something wrong with", hitter['name_display_first_last'])
			continue
		print(hitter['name_display_first_last'], "is a batter and had", len(batter_logs), "appearances in", year)
		team_batter_logs.append(batter_logs)

	return (pd.concat(team_pitcher_logs), pd.concat(team_batter_logs))

def scrape_player_stats(year=2017):
	teams = get_teams(year)
	pitchers_list, batters_list = [], []
	for team in teams:
		print(team['name'])
		pitchers_df, batters_df = get_team_logs(year,team['id'])
		pitchers_list.append(pitchers_df)
		batters_list.append(batters_df)
	return (pd.concat(pitchers_list).set_index(['player_id','game_id']),pd.concat(batters_list).set_index(['player_id','game_id']))


if __name__ == '__main__':
	year = 2017
	pitcher_df, batter_df = scrape_player_stats(year=year)
	csv_path_pitchers = os.path.join('..','data','player_logs','pitchers_{}.csv'.format(year))
	pitcher_df.drop_duplicates().to_csv(csv_path_pitchers)
	csv_path_batters = os.path.join('..','data','player_logs','batters_{}.csv'.format(year))
	batter_df.drop_duplicates().to_csv(csv_path_batters)
