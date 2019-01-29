import pandas as pd
import os
import json
from operator import itemgetter
from scraper_utils import get_soup, fangraphs_to_mlb, get_days_in_season

manifest = pd.read_csv(os.path.join('..','data','master2.csv'), encoding='latin1')
manifest2 = pd.read_csv(os.path.join('..','data','master3.csv'), encoding='latin1')

with open(os.path.join('..','data','minor_league_equivalencies_2018.json')) as f:
	pfs = json.load(f)
with open(os.path.join('..','data','lgmults.json')) as f:
	lgMults = json.load(f)
with open(os.path.join('..','data','minor_league_teams_2018.json')) as f:
	leagues = json.load(f)

base = "https://www.fangraphs.com/"

def batter_minor_league_adj(line, mult, pfs):
	pkLine = {}
	for nstat in ['bb', 'k', 'hbp']:
		pkLine[nstat] = line[nstat]
	for dstat in ['double', 'triple']:
		pkLine[dstat] = line[dstat]*pfs['D']
	for hstat in ['single']:
		pkLine[hstat] = line[hstat]*pfs['H']
	for hrstat in ['hr']:
		pkLine[hrstat] = line[hrstat]*pfs['HR']
	adjLine = {
		"triple": pkLine["triple"] * (mult ** 0.75),
		"hr": pkLine["hr"] * (mult ** 0.75),
		"bb": pkLine["bb"] * (mult ** 0.75),
		"hbp": pkLine["hbp"] * (mult ** 0.75),
		"single": pkLine["single"] * (mult ** 0.4),
		"double": pkLine["double"] * (mult ** 0.5),
		"k": pkLine["k"] / (mult ** 0.2)
	}
	adjLine['pa'] = adjLine['single'] + adjLine['double'] + adjLine['triple'] + \
					adjLine['hr'] + adjLine['bb'] + adjLine['hbp'] + adjLine['k'] + \
					line['pa'] - (line['single'] + line['double'] + \
									line['triple'] + line['hr'] + \
									line['bb'] + line['hbp'] + line['k'])

	adjLine['name'] = line['name']
	adjLine['date'] = line['date']
	adjLine['mlb_id'] = line['mlb_id']
	adjLine['key'] = line['key']
	return adjLine

def pitcher_minor_league_adj(line, mult, pfs):
	pkLine = {}
	for nstat in ['bb', 'k', 'hbp']:
		pkLine[nstat] = line[nstat]

	for hstat in ['h']:
		pkLine[hstat] = line[hstat]*1/pfs['H']

	for hrstat in ['hr']:
		pkLine[hrstat] = line[hrstat]*1/pfs['HR']
	adjLine = {
		"hr": pkLine["hr"] / (mult ** 0.75),
		"bb": pkLine["bb"] / (mult ** 0.75),
		"hbp": pkLine["hbp"] / (mult ** 0.75),
		"h": pkLine["h"] / (mult ** 0.4),
		"k": pkLine["k"] * (mult ** 0.2)
	}

	adjLine['tbf'] = adjLine['h'] + adjLine['hr'] + adjLine['bb'] + \
					adjLine['hbp'] + adjLine['k'] + line['tbf'] - \
						(line['h'] + line['hr'] + line['bb'] + \
						line['hbp'] + line['k'])

	adjLine['name'] = line['name']
	adjLine['date'] = line['date']
	adjLine['mlb_id'] = line['mlb_id']
	adjLine['key'] = line['key']
	return adjLine

def get_key(tds, minor_league = False):
	date = tds[0].text
	away = tds[1].text[:3] if '@' in tds[2].text else tds[2].text
	home = tds[1].text[:3] if '@' not in tds[2].text else tds[2].text.replace('@','')
	lg = 'milb' if minor_league else 'mlb'
	key = date.replace('-','/')+'/'+fangraphs_to_mlb[away]+lg+'-'+fangraphs_to_mlb[home]+lg
	if minor_league:
		key = key + '-1'
	else:
		key = key + '-1' if 'dh=2' not in tds[0].a['href'] else key + '-2'
	return key

def match_id_to_mlb(name, fangraphs_id):
	try:
		row = manifest[manifest['IDFANGRAPHS'] == fangraphs_id]
		return int(row['MLBID'].iloc[0]), row['FANGRAPHSNAME'].iloc[0]
	except:
		try:
			row = manifest2[manifest2['fg_id'] == fangraphs_id]
			return int(row['mlb_id'].iloc[0]), row['mlb_name'].iloc[0]
		except:
			return None, None

def get_player_major_league_soup(links, year):
	for link in links:
		logs_link = base + link.replace('statss','statsd') + '&gds=&gde=&type=1&season={}'.format(year)
		yield get_soup(logs_link)

def get_player_minor_league_soup(links, year):
	for link in links:
		logs_link = base + link.replace('statss','statsd') + '&gds=&gde=&type=-1&season={}'.format(year)
		yield get_soup(logs_link, check_500 = True)

def get_batter_stats(batters, year):
	all_batter_stats = []
	for soup in get_player_minor_league_soup(batters, year):
		if soup is None:
			continue
		name = soup.find('div', {'class', 'player-info-box-name'}).h1.text
		print(name)
		player_id = soup.find('div', {'class', 'player-info-bio'}).find('a')['href'].split('playerid=')[1].split('&')[0]
		mlb_id, name = match_id_to_mlb(name, player_id)
		print(mlb_id, name)
		table = soup.find('table', {'class', 'rgMasterTable'}).tbody
		rows = table.findAll('tr', {'class', 'rgRow'})[1:] + table.findAll('tr', {'class', 'rgAltRow'})
		for tr in rows:
			game_info = {}
			tds = tr.findAll('td')
			game_info['name'] = name
			game_info['mlb_id'] = mlb_id
			game_info['key'] = get_key(tds, minor_league = True)
			game_info['date'] = tds[0].text
			game_info['pa'] = int(tds[5].text)
			game_info['single'] = int(tds[7].text)
			game_info['double'] = int(tds[8].text)
			game_info['triple'] = int(tds[9].text)
			game_info['hr'] = int(float(tds[10].text))
			game_info['bb'] = int(tds[13].text)
			game_info['k'] = int(tds[15].text)
			game_info['hbp'] = int(tds[16].text)
			team = tds[1].text
			if team not in pfs.keys():
				print(team, "not a recognized minor league team")
				continue
			all_batter_stats.append(batter_minor_league_adj(game_info, lgMults[leagues[team]], pfs[team]))

	for soup in get_player_major_league_soup(batters, year):
		if soup is None:
			continue
		name = soup.find('div', {'class', 'player-info-box-name'}).h1.text
		player_id = soup.find('div', {'class', 'player-info-bio'}).find('a')['href'].split('playerid=')[1].split('&')[0]
		mlb_id, name = match_id_to_mlb(name, player_id)
		print(mlb_id, name)
		table = soup.find('table', {'class', 'rgMasterTable'}).tbody
		rows = table.findAll('tr', {'class', 'rgRow'})[1:] + table.findAll('tr', {'class', 'rgAltRow'})
		for tr in rows:
			game_info = {}
			tds = tr.findAll('td')
			game_info['name'] = name
			game_info['mlb_id'] = mlb_id
			game_info['key'] = get_key(tds)
			game_info['date'] = tds[0].a.text
			game_info['pa'] = int(tds[7].text)
			game_info['single'] = int(tds[9].text)
			game_info['double'] = int(tds[10].text)
			game_info['triple'] = int(tds[11].text)
			game_info['hr'] = int(tds[12].text)
			game_info['bb'] = int(tds[15].text)
			game_info['k'] = int(tds[17].text)
			game_info['hbp'] = int(tds[18].text)

			all_batter_stats.append(game_info)

	logs_df = pd.DataFrame(all_batter_stats).sort_values(by=['mlb_id', 'key'])
	logs_df = logs_df[['mlb_id','key','name','date','pa','single','double','triple','hr','bb','hbp','k']]
	print(logs_df)
	return logs_df

def get_pitcher_stats(pitchers, year):
	all_pitcher_stats = []
	for soup in get_player_major_league_soup(pitchers, year):
		if soup is None:
			continue
		name = soup.find('div', {'class', 'player-info-box-name'}).h1.text
		player_id = soup.find('div', {'class', 'player-info-bio'}).find('a')['href'].split('playerid=')[1].split('&')[0]
		mlb_id, name = match_id_to_mlb(name, player_id)
		print(mlb_id, name)
		table = soup.find('table', {'class', 'rgMasterTable'}).tbody
		rows = table.findAll('tr', {'class', 'rgRow'})[1:] + table.findAll('tr', {'class', 'rgAltRow'})
		for tr in rows:
			game_info = {}
			game_info['name'] = name
			game_info['mlb_id'] = mlb_id
			tds = tr.findAll('td')
			key = get_key(tds)
			game_info['key'] = key
			game_info['date'] = tds[0].a.text
			game_info['tbf'] = int(tds[15].text)
			if game_info['tbf'] == 0:
				continue
			game_info['h'] = int(tds[16].text) - int(tds[19].text)
			game_info['hr'] = int(tds[19].text)
			game_info['bb'] = int(tds[20].text)
			game_info['hbp'] = int(tds[22].text)
			game_info['k'] = int(tds[25].text)

			all_pitcher_stats.append(game_info)
			
	for soup in get_player_minor_league_soup(pitchers, year):
		if soup is None:
			continue
		name = soup.find('div', {'class', 'player-info-box-name'}).h1.text
		player_id = soup.find('div', {'class', 'player-info-bio'}).find('a')['href'].split('playerid=')[1].split('&')[0]
		mlb_id, name = match_id_to_mlb(name, player_id)
		print(mlb_id, name)
		table = soup.find('table', {'class', 'rgMasterTable'}).tbody
		rows = table.findAll('tr', {'class', 'rgRow'})[1:] + table.findAll('tr', {'class', 'rgAltRow'})
		for tr in rows:
			game_info = {}
			game_info['name'] = name
			game_info['mlb_id'] = mlb_id
			tds = tr.findAll('td')
			game_info['key'] = get_key(tds, minor_league = True)
			game_info['date'] = tds[0].text
			game_info['tbf'] = int(tds[11].text)
			if game_info['tbf'] == 0:
				continue
			game_info['h'] = int(tds[12].text) - int(tds[15].text)
			game_info['hr'] = int(tds[15].text)
			game_info['bb'] = int(tds[16].text)
			game_info['hbp'] = int(tds[18].text)
			game_info['k'] = int(tds[21].text)
			team = tds[1].text
			if team not in pfs.keys():
				print(team, "not a recognized minor league team")
				continue
			all_pitcher_stats.append(pitcher_minor_league_adj(game_info, lgMults[leagues[team]], pfs[team]))

	logs_df = pd.DataFrame(all_pitcher_stats).sort_values(by=['mlb_id', 'key'])
	logs_df = logs_df[['mlb_id','key','name','date','tbf','h','hr','bb','hbp','k']]
	print(logs_df)
	return logs_df

def get_player_ids(year, days):
	all_game_links = []
	for day in days:
		print(day)
		day_url = base + "scoreboard.aspx?date=" + day
		day_soup = get_soup(day_url, check_500 = True)
		if day_soup is None:
			continue
		all_game_links.extend([str(a['href']).replace(' ', '%20') for a in day_soup.findAll('a', href=True) if 'boxscore.aspx' in a['href']])

	print()
	all_batter_links = []
	all_pitcher_links = []
	for game_link in all_game_links:
		print(game_link)
		game_url = base + game_link
		game_soup = get_soup(game_url)
		home_batters = game_soup.find('div', {'id': 'WinsBox1_dghb'}).findAll('a', href=True)
		away_batters = game_soup.find('div', {'id': 'WinsBox1_dgab'}).findAll('a', href=True)
		home_pitchers = game_soup.find('div', {'id': 'WinsBox1_dghp'}).findAll('a', href=True)
		away_pitchers = game_soup.find('div', {'id': 'WinsBox1_dgap'}).findAll('a', href=True)
		all_batter_links.extend([b['href'] for b in home_batters + away_batters if 'position=P' not in b])
		all_pitcher_links.extend([p['href'] for p in home_pitchers + away_pitchers if 'position=P' in p])
	all_batter_links = list(set(all_batter_links))
	all_pitcher_links = list(set(all_pitcher_links))
	batter_stats = get_batter_stats(all_batter_links, year)
	pitcher_stats = get_pitcher_stats(all_pitcher_links, year)
	return batter_stats, None

if __name__ == '__main__':
	year = 2018
	# all_batter_links = []
	# url = base + "leaders.aspx?pos=np&stats=bat&lg=all&qual=0&type=8&season={}&month=0&season1={}&ind=0&team=0&rost=0&age=0&filter=&players=0&page=1_1000".format(year, year)
	# player_rows = get_soup(url).find('table', {'class', 'rgMasterTable'}).tbody.findAll('a')
	# for item in player_rows:
	# 	if not item.has_attr('href') or not item['href'].startswith('statss') or 'position=P' in item['href']:
	# 		continue
	# 	all_batter_links.append(item['href'])
	# batter_stats = get_batter_stats(all_batter_links, year)
	# csv_path = os.path.join('..','data','player_logs','batter_logs_{}_fan.csv'.format(year))
	# batter_stats.to_csv(csv_path, index = False)

	all_pitcher_links = []
	url = "https://www.fangraphs.com/leaders.aspx?pos=all&stats=pit&lg=all&qual=0&type=8&season={}&month=0&season1={}&ind=0&team=0&rost=0&age=0&filter=&players=0&page=1_1000".format(year, year)
	player_rows = get_soup(url).find('table', {'class', 'rgMasterTable'}).tbody.findAll('a')
	for item in player_rows:
		# get rid of extraneous links and non pitchers
		if not item.has_attr('href') or not item['href'].startswith('statss') or 'position=P' not in item['href']:
			# do not continue on Shohei Ohtani
			if '19755' not in item['href']:
				continue
		all_pitcher_links.append(item['href'].replace('position=DH','position=P'))
	pitcher_stats = get_pitcher_stats(all_pitcher_links, year)
	csv_path = os.path.join('..','data','player_logs','pitcher_logs_{}_fan.csv'.format(year))
	pitcher_stats.to_csv(csv_path, index = False)
