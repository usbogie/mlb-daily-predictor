import pandas as pd
import os
from operator import itemgetter
from scraper_utils import get_soup, fangraphs_to_mlb, get_days_in_season

manifest = pd.read_csv(os.path.join('..','data','master2.csv'), encoding='latin1')
manifest2 = pd.read_csv(os.path.join('..','data','master3.csv'), encoding='latin1')

base = "https://www.fangraphs.com/"

def get_key(tds, minor_league = False):
	date = tds[0].a.text
	away = tds[1].text if '@' in tds[2].text else tds[2].text
	home = tds[1].text if '@' not in tds[2].text else tds[2].text.replace('@','')
	lg = 'milb' if minor_league else 'mlb'
	key = date.replace('-','/')+'/'+fangraphs_to_mlb[away]+lg+'-'+fangraphs_to_mlb[home]
	key = key + lg + '-1' if 'dh=2' not in tds[0].a['href'] else key + lg + '-2'
	return key

def match_id_to_mlb(name, fangraphs_id):
	try:
		row = manifest[manifest['IDFANGRAPHS'] == fangraphs_id]
		return int(row['MLBID'].iloc[0]), row['MLBNAME'].iloc[0]
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
		yield get_soup(logs_link)

def get_batter_stats(batters, year):
	all_batter_stats = []
	for soup in get_player_major_league_soup(batters, year):
		if soup is None:
			continue
		name = soup.find('div', {'class', 'player-info-box-name'}).h1.text
		player_id = soup.find('div', {'class', 'player-info-bio'}).find('a')['href'].split('playerid=')[1].split('&')[0]
		mlb_id, name = match_id_to_mlb(name, player_id)
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

	for soup in get_player_minor_league_soup(batters, year):
		if soup is None:
			continue
		name = soup.find('div', {'class', 'player-info-box-name'}).h1.text
		player_id = soup.find('div', {'class', 'player-info-bio'}).find('a')['href'].split('playerid=')[1].split('&')[0]
		mlb_id, name = match_id_to_mlb(name, player_id)
		table = soup.find('table', {'class', 'rgMasterTable'}).tbody
		rows = table.findAll('tr', {'class', 'rgRow'})[1:] + table.findAll('tr', {'class', 'rgAltRow'})
		for tr in rows:
			game_info = {}
			tds = tr.findAll('td')

			game_info['name'] = name
			game_info['mlb_id'] = mlb_id
			game_info['key'] = get_key(tds, minor_league = True)
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

# def get_pitcher_stats(pitchers, year):


def get_player_ids(year, days):
	all_game_links = []
	for day in days:
		day_url = base + "scoreboard.aspx?date=" + day
		day_soup = get_soup(day_url)
		all_game_links.extend([str(a['href']).replace(' ', '%20') for a in day_soup.findAll('a', href=True) if 'boxscore.aspx' in a['href']])
		break

	print(all_game_links)
	all_batter_ids = []
	all_pitcher_ids = []
	for game_link in all_game_links:
		print(game_link)
		game_url = base + game_link
		game_soup = get_soup(game_url)
		home_batters = game_soup.find('div', {'id': 'WinsBox1_dghb'}).findAll('a', href=True)
		away_batters = game_soup.find('div', {'id': 'WinsBox1_dgab'}).findAll('a', href=True)
		home_pitchers = game_soup.find('div', {'id': 'WinsBox1_dghp'}).findAll('a', href=True)
		away_pitchers = game_soup.find('div', {'id': 'WinsBox1_dgap'}).findAll('a', href=True)
		all_batter_ids.extend([b['href'] for b in home_batters + away_batters if 'position=P' not in b])
		all_pitcher_ids.extend([p['href'] for p in home_pitchers + away_pitchers if 'position=P' in p])
		break
	all_batter_ids = list(set(all_batter_ids))
	all_pitcher_ids = list(set(all_pitcher_ids))
	batter_stats = get_batter_stats(all_batter_ids, year)

if __name__ == '__main__':
	year = 2018
	player_links = get_player_ids(year, get_days_in_season(year))
	print(len(player_links))

	# df = scrape_pitcher_logs(year)
	# csv_path = os.path.join('..','data','player_logs','pitcher_logs_{}.csv'.format(year))
	# df = scrape_batter_logs(year)
	# csv_path = os.path.join('..','data','player_logs','batter_logs_{}.csv'.format(year))
	# df.to_csv(csv_path)
