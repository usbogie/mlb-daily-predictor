import pandas as pd
import os
from operator import itemgetter
from scraper_utils import get_soup, fangraphs_to_mlb, get_days_in_season

manifest = pd.read_csv(os.path.join('..','data','master2.csv'), encoding='latin1')
manifest2 = pd.read_csv(os.path.join('..','data','master3.csv'), encoding='latin1')

base = "https://www.fangraphs.com/"

def get_batting_stats(batters):
    batting_stats = []
    for tr in batters:
        tds = tr.findAll('td')
        batter_stats = dict(
            name = tds[0].a.text,
            id = tds[0].a['href'].split('?playerid=')[1].split('&')[0],
            pa = int(tds[2].text) - int(tds[11].text),
            single = int(tds[4].text),
            double = int(tds[5].text),
            triple = int(tds[6].text),
            hr = int(tds[7].text),
            bb = int(tds[10].text),
            k = int(tds[13].text),
            hbp = int(tds[12].text),
        )
        batting_stats.append(batter_stats)
    return batting_stats

def get_pitching_stats(pitchers, game_logs):
    pitching_stats = []
    for tr in pitchers:
        tds = tr.findAll('td')
        pitcher_hits = int(tds[13].text)
        pitcher_id = tds[0].a['href'].split('?playerid=')[1].split('&')[0]
        singles = doubles = triples = 0
        for log in game_logs:
            if pitcher_id in str(log.findAll('td')[0]):
                event = str(log.findAll('td')[6].text)
                if 'singled' in event:
                    singles = singles + 1
                if 'doubled' in event:
                    doubles = doubles + 1
                if 'tripled' in event:
                    triples = triples + 1

        pitcher_stats = dict(
            name = tds[0].a.text,
            id = tds[0].a['href'].split('?playerid=')[1].split('&')[0],
            tbf = int(tds[12].text) - int(tds[18].text),
            single = singles,
            double = doubles,
            triple = triples,
            hr = int(tds[16].text),
            bb = int(tds[17].text),
            hbp = int(tds[19].text),
            k = int(tds[22].text),
        )
        pitching_stats.append(pitcher_stats)
    return pitching_stats

def get_player_ids(year, days):
    all_game_links = []
    for day in days:
        day_url = base + "scoreboard.aspx?date=" + day
        day_soup = get_soup(day_url)
        all_game_links.extend([str(a['href']).replace(' ', '%20') for a in day_soup.findAll('a', href=True) if 'boxscore.aspx' in a['href']])
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
        game_logs = game_soup.find('div', {'id': 'WinsBox1_dgPlay'}).table.tbody.findAll('tr')
        pitcher_stats = get_pitching_stats(home_pitchers + away_pitchers, game_logs)
        all_batter_stats.extend(batter_stats)
        all_pitcher_stats.extend(pitcher_stats)
    



if __name__ == '__main__':
    year = 2018
    player_links = get_player_ids(year, get_days_in_season(year))
    print(len(player_links))

	# df = scrape_pitcher_logs(year)
	# csv_path = os.path.join('..','data','player_logs','pitcher_logs_{}.csv'.format(year))
	# df = scrape_batter_logs(year)
	# csv_path = os.path.join('..','data','player_logs','batter_logs_{}.csv'.format(year))
	# df.to_csv(csv_path)
