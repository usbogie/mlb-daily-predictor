import pandas as pd
import os
from operator import itemgetter
from scraper_utils import get_soup, fangraphs_to_mlb, get_days_in_season

manifest = pd.read_csv(os.path.join('..','data','master2.csv'), encoding='latin1')
manifest2 = pd.read_csv(os.path.join('..','data','master3.csv'), encoding='latin1')

base = "https://www.fangraphs.com/"

def get_key(tds):
	date = tds[0].a.text
	away = tds[1].text if '@' in tds[2].text else tds[2].text
	home = tds[1].text if '@' not in tds[2].text else tds[2].text.replace('@','')
	key = date.replace('-','/')+'/'+fangraphs_to_mlb[away]+'mlb-'+fangraphs_to_mlb[home]
	key = key+'mlb-1' if 'dh=2' not in tds[0].a['href'] else key+'mlb-2'
	return key

def get_game_log_rows(url):
	soup = get_soup(url)
	table = soup.find('table', {'class', 'rgMasterTable'}).tbody
	rows = table.findAll('tr', {'class', 'rgRow'})[1:] + table.findAll('tr', {'class', 'rgAltRow'})
	return (soup, rows)

def match_id_to_mlb(name, fangraphs_id):
	try:
		row = manifest2[manifest2['fg_id'] == fangraphs_id]
		return int(row['mlb_id'].iloc[0]), row['mlb_name'].iloc[0]
	except:
		try:
			row = manifest[manifest['IDFANGRAPHS'] == fangraphs_id]
			return int(row['MLBID'].iloc[0]), row['MLBNAME'].iloc[0]
		except:
			return None, None

def get_pitcher_standard_stats(url):
	soup, rows = get_game_log_rows(url)
	name = soup.find('div', {'class', 'player-info-box-name'}).h1.text
	print(name)
	pos = soup.find('div', {'class', 'player-info-box-pos'}).text
	if pos != 'P' and name != 'Shohei Ohtani':
		return None, name
	mlb_id, mlb_name = match_id_to_mlb(name, url.split('playerid=')[1].split('&')[0])
	if mlb_id is None:
		return None, name
	games = {}
	keys_w_no_batters = []
	for tr in rows:
		game_info = {}
		game_info['name'] = mlb_name
		game_info['mlb_id'] = mlb_id
		tds = tr.findAll('td')
		key = get_key(tds)
		game_info['key'] = key
		game_info['date'] = tds[0].a.text
		game_info['tbf'] = int(tds[15].text)
		if game_info['tbf'] == 0:
			keys_w_no_batters.append(key)
		game_info['gs'] = bool(int(tds[8].text))
		game_info['hr'] = int(tds[19].text)
		game_info['bb'] = int(tds[20].text)
		game_info['hbp'] =int(tds[22].text)
		game_info['k'] = int(tds[25].text)
		games[key] = game_info
	return games, keys_w_no_batters

def get_pitcher_batted_ball_stats(url, game_dict, keys_w_no_batters):
	soup, rows = get_game_log_rows(url)
	games = []
	for tr in rows:
		tds = tr.findAll('td')
		key = get_key(tds)
		if key in keys_w_no_batters:
			print('No batters for', key)
			continue
		game_info = game_dict[key]
		game_info['ld'] = int(tds[6].text)
		game_info['gb'] = int(tds[4].text)
		game_info['fb'] = int(tds[5].text)
		game_info['iffb'] = int(tds[7].text)
		games.append(game_info)
	games = sorted(games, key=itemgetter('key'))
	return pd.DataFrame(games)

def scrape_pitcher_logs(year):
	urls = []
	url = "https://www.fangraphs.com/leaders.aspx?pos=all&stats=pit&lg=all&qual=0&type=8&season={}&month=0&season1={}&ind=0&team=0&rost=0&age=0&filter=&players=0&page=1_1000".format(year, year)
	player_rows = get_soup(url).find('table', {'class', 'rgMasterTable'}).tbody.findAll('a')
	for item in player_rows:
		if item.has_attr('href') and item['href'].startswith('statss'):
			urls.append(item['href'])
	dfs = []
	missing_players = []
	for ix, url in enumerate(urls):
		print(ix, end=" - ")
		url = url.replace('statss', 'statsd')
		url = url.replace('DH', 'P') if 'position=DH' in url else url
		standard_url = base + url + "&gds=&gde=&type=1&season=" + str(year)
		games, keys_w_no_batters = get_pitcher_standard_stats(standard_url)
		if games is None:
			print("Player not in MAP or non-pitcher, continue")
			missing_players.append(keys_w_no_batters)
			continue
		bb_url = base + url + "&gds=&gde=&type=4&season=" + str(year)
		df = get_pitcher_batted_ball_stats(bb_url, games, keys_w_no_batters)
		dfs.append(df)
	print(missing_players)
	df = pd.concat(dfs)
	df = df[['name', 'key', 'date', 'mlb_id', 'gs', 'gb', 'fb', 'ld', 'iffb', 'tbf', 'hr', 'bb', 'hbp', 'k']]
	return df.set_index(['mlb_id', 'date'])

def get_batter_standard_stats(url):
	soup, rows = get_game_log_rows(url)
	name = soup.find('div', {'class', 'player-info-box-name'}).h1.text
	print(name)
	if soup.find('div', {'class', 'player-info-box-pos'}).text == 'P':
		return None
	mlb_id, name = match_id_to_mlb(name, url.split('playerid=')[1].split('&')[0])
	games = {}
	for tr in rows:
		game_info = {}
		game_info['name'] = name
		tds = tr.findAll('td')
		key = get_key(tds)
		game_info['mlb_id'] = mlb_id
		game_info['key'] = key
		game_info['date'] = tds[0].a.text
		game_info['team'] = fangraphs_to_mlb[tds[2].text.replace('@','')]
		game_info['pa'] = int(tds[7].text)
		game_info['hr'] = int(tds[12].text)
		game_info['bb'] = int(tds[15].text)
		game_info['k'] = int(tds[17].text)
		game_info['hbp'] = int(tds[18].text)
		games[key] = game_info
	return games

def get_batter_advanced_stats(url, game_dict):
	_, rows = get_game_log_rows(url)
	for tr in rows:
		tds = tr.findAll('td')
		key = get_key(tds)
		game_dict[key]['wRAA'] = float(tds[17].text)
	return game_dict

def scrape_batter_logs(year):
	urls = []
	url = base + "leaders.aspx?pos=np&stats=bat&lg=all&qual=0&type=8&season={}&month=0&season1={}&ind=0&team=0&rost=0&age=0&filter=&players=0&page=1_1000".format(year, year)
	player_rows = get_soup(url).find('table', {'class', 'rgMasterTable'}).tbody.findAll('a')
	for item in player_rows:
		if not item.has_attr('href') or not item['href'].startswith('statss'):
			continue
		urls.append(item['href'])

	print(len(urls))
	print(urls[0])
	dfs = []
	for ix, url in enumerate(urls):
		print(ix, end=" - ")
		url = url.replace('statss', 'statsd')
		standard_url = base + url + "&gds=&gde=&type=1&season=" + str(year)
		games = get_batter_standard_stats(standard_url)
		if games is None:
			print("Pitcher, skipping")
			continue
		advanced_url = base + url + "&gds=&gde=&type=2&season=" + str(year)
		games = get_batter_advanced_stats(advanced_url, games)
		df = pd.DataFrame(list(games.values()))[::-1]
		dfs.append(df)
	df = pd.concat(dfs)
	print(df)
	df = df[['mlb_id', 'date', 'name', 'key', 'team', 'pa', 'bb', 'k', 'hbp', 'hr', 'wRAA']]
	return df.set_index(['mlb_id','date'])

if __name__ == '__main__':
	year = 2018
	df = scrape_pitcher_logs(year)
	csv_path = os.path.join('..','data','player_logs','pitcher_logs_{}.csv'.format(year))
	# df = scrape_batter_logs(year)
	# csv_path = os.path.join('..','data','player_logs','batter_logs_{}.csv'.format(year))
	df.to_csv(csv_path)
