import pandas as pd
import os
from scrapers.scraper_utils import team_codes

year = 2018

retro_path = os.path.join('data', 'retrosheet', str(year))

def parse_team_log(log_file, team):
	i = 0
	game_lines = []
	games = []
	for line in log_file:
		#print(repr(line))
		if line.startswith('id,{}'.format(team)):
			games.append(list(game_lines))
			game_lines = []
		game_lines.append(line.rstrip())
	games.append(game_lines)
	return games[1:]

def determine_event(outcome):
	if outcome.startswith('SB'):
		return None
	elif outcome.startswith('S'):
		return 'single'
	elif outcome.startswith('D'):
		return 'double'
	elif outcome.startswith('T'):
		return 'triple'
	elif outcome.startswith('HP'):
		return 'hitbypitch'
	elif outcome.startswith('H') or outcome.startswith('HR'):
		return 'homerun'
	elif outcome.startswith('E') or outcome.startswith('FC'):
		return 'NonKOut'
	elif outcome.startswith('I') or outcome.startswith('IW'):
		return 'ibb'
	elif outcome.startswith('W'):
		return 'bb'
	elif outcome.startswith('K'):
		return 'k'
	elif outcome[0].isdigit():
		return 'NonKOut'
	else:
		return None

def get_matchups(games):
	matchups = []
	for game in games:
		away = game[2][-3:].lower()
		home = game[3][-3:].lower()
		date = game[5][-10:]
		double = '2' if game[6][-1:] == '2' else '1'
		key = '{}/{}mlb-{}mlb-{}'.format(date, away, home, double)
		dh = True if game[9] == 'info,usedh,true' else False
		if dh:
			away_p = game[37][6:14]
			home_p = game[47][6:14]
		else:
			away_p = [x for x in game[28:37] if x[-1] == '1'][0][6:14]
			home_p = [x for x in game[37:46] if x[-1] == '1'][0][6:14]
		start = 48 if dh else 46
		for event in game[start:]:
			if event.startswith('sub'):
				position = event[-5:].split(',')
				if position[2] == '1':
					#pitching change
					if position[0] == '0':
						away_p = event[4:12]
					if position[0] == '1':
						home_p = event[4:12]
			if event.startswith('play'):
				parts = event.split(',')
				matchup = dict(
					pitcher = away_p if parts[2] == '1' else home_p,
					batter = parts[3],
					outcome = determine_event(parts[6]),
					date = date.replace('/', '-'),
					key = key
				)
				if matchup['outcome'] is not None:
					matchups.append(matchup)
	return matchups


if __name__ == '__main__':
	teams = list(team_codes.values())
	all_matchups = []
	for team in teams:
		try:
			log_file = open(os.path.join(retro_path, '{}{}.EVA'.format(year, team.upper())), 'r')
		except:
			log_file = open(os.path.join(retro_path, '{}{}.EVN'.format(year, team.upper())), 'r')
		games = parse_team_log(log_file, team.upper())
		matchups = get_matchups(games)
		all_matchups.extend(matchups)
	df = pd.DataFrame(all_matchups)
	print(df)
	df.to_csv(os.path.join(retro_path, '{}_matchups.csv'.format(year)), index=False)
