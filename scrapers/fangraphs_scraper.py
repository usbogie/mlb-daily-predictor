import pandas as pd
import os
from operator import itemgetter
from scraper_utils import get_soup, fangraphs_to_mlb, get_days_in_season

manifest = pd.read_csv(os.path.join('..','data','master2.csv'), encoding='latin1')
manifest2 = pd.read_csv(os.path.join('..','data','master3.csv'), encoding='latin1')

base = "https://www.fangraphs.com/"

def get_player_ids(year, days):
    all_game_links = []
    for day in days:
        day_url = base + "scoreboard.aspx?date=" + day
        day_soup = get_soup(day_url)
        all_game_links += [str(a['href']).replace(' ', '%20') for a in day_soup.findAll('a', href=True) if 'boxscore.aspx' in a['href']]
        break

    print(all_game_links)
    all_batter_stats = []
    all_pitcher_stats = []
    for game_link in all_game_links:
        print(game_link)
        game_url = base + game_link
        game_soup = get_soup(game_url)
        home_batters = game_soup.find('div', {'id': 'WinsBox1_dg2hb'}).table.tbody.findAll('tr')[:-1]
        away_batters = game_soup.find('div', {'id': 'WinsBox1_dg2ab'}).table.tbody.findAll('tr')[:-1]
        home_pitchers = game_soup.find('div', {'id': 'WinsBox1_dg2hp'}).table.tbody.findAll('tr')[:-1]
        away_pitchers = game_soup.find('div', {'id': 'WinsBox1_dg2ap'}).table.tbody.findAll('tr')[:-1]
        batter_stats = get_batting_stats(home_batters + away_batters)
        pitcher_stats = get_pitching_stats(home_batters + away_batters)



if __name__ == '__main__':
    year = 2018
    player_links = get_player_ids(year, get_days_in_season(2018))
    print(len(player_links))

	# df = scrape_pitcher_logs(year)
	# csv_path = os.path.join('..','data','player_logs','pitcher_logs_{}.csv'.format(year))
	# df = scrape_batter_logs(year)
	# csv_path = os.path.join('..','data','player_logs','batter_logs_{}.csv'.format(year))
	# df.to_csv(csv_path)
