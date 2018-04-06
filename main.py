from datetime import datetime
from scrapers.scraper_utils import team_codes
from storage.Game import Game
from simulation.MonteCarlo import MonteCarlo
import pandas as pd
import os
import sys

def calc_averages():
    avgs_dict = dict()
    steamer_batters = pd.read_csv(os.path.join('data','steamer','steamer_hitters_2018.csv'))
    total_PA = steamer_batters['PA'].sum()
    avgs_dict['1B'] = steamer_batters['1B'].sum() / float(total_PA)
    avgs_dict['2B'] = steamer_batters['2B'].sum() / float(total_PA)
    avgs_dict['3B'] = steamer_batters['3B'].sum() / float(total_PA)
    avgs_dict['HR'] = steamer_batters['HR'].sum() / float(total_PA)
    avgs_dict['NIBB'] = steamer_batters['NIBB'].sum() / float(total_PA)
    avgs_dict['HBP'] = steamer_batters['HBP'].sum() / float(total_PA)
    avgs_dict['K'] = steamer_batters['K'].sum() / float(total_PA)
    return avgs_dict

def get_batting_stats(lineup):
    lineup_stats = []
    avg_pitcher_stats = {'PA': 5277, '1B': 464, '2B': 79, '3B': 7, 'HR': 27,
                         'NIBB': 162, 'HBP': 16, 'K': 2028}
    steamer_batters = pd.read_csv(os.path.join('data','steamer','steamer_hitters_2018.csv'))
    for i in range(1,10):
        batter_name = lineup.iloc[0][str(i)]
        row = steamer_batters.loc[(steamer_batters['firstname'] == batter_name.split()[0]) & \
                                  (steamer_batters['lastname'] == batter_name.split()[1]) & \
                                  (steamer_batters['Team'] == team_codes[lineup.iloc[0]['name']].upper())].to_dict('list')
        if len(row['mlbamid']) == 0:
            print(batter_name, "is probably a pitcher, giving him average pitcher stats")
            lineup_stats.append(dict(avg_pitcher_stats))
            break
        ans = 'a'
        for key, val in row.items():
            if len(val) > 1 and ans != 'y':
                print("DUPLICATE something is wrong")
                print(row)
                ans = input("Would you like to select the first player y/n => ")
                if ans == 'n':
                    sys.exit()
            row[key] = val[0]
        lineup_stats.append(row)
    return lineup_stats

def get_pitching_stats(lineup):
    lineup_stats = []
    steamer_pitchers = pd.read_csv(os.path.join('data','steamer','steamer_pitchers_2018.csv'))
    pitcher_name = lineup.iloc[0]['10']
    starting_pitcher = steamer_pitchers.loc[(steamer_pitchers['firstname'] == pitcher_name.split()[0]) & \
                                  (steamer_pitchers['lastname'] == pitcher_name.split()[1]) & \
                                  (steamer_pitchers['DBTeamId'] == team_codes[lineup.iloc[0]['name']].upper())].to_dict('list')
    relief_pitchers = steamer_pitchers.loc[(steamer_pitchers['relief_IP'] >= 10.0) & \
                                           ((steamer_pitchers['DBTeamId'] == team_codes[lineup.iloc[0]['name']].upper()))]

    for key, val in starting_pitcher.items():
        if len(val) > 1:
            print("DUPLICATE something is wrong")
            sys.exit()
        starting_pitcher[key] = val[0]

    return [starting_pitcher] + list(relief_pitchers.T.to_dict().values())

def main():
    today = datetime.now().strftime('%Y-%m-%d')
    averages = calc_averages()
    games = pd.read_csv(os.path.join('data','lines','today.csv'))
    lineups = pd.read_csv(os.path.join('data','lineups','today.csv'))
    for index, game in games.iterrows():
        game_obj = Game(game['date'],game['time'],game['away'],game['home'])
        away_lineup = lineups.loc[(lineups['key'] == game['key']) & (game['away'] == lineups['name'])]
        home_lineup = lineups.loc[(lineups['key'] == game['key']) & (game['home'] == lineups['name'])]
        away_lineup_stats = get_batting_stats(away_lineup)
        home_lineup_stats = get_batting_stats(home_lineup)
        away_pitching = get_pitching_stats(away_lineup)
        home_pitching = get_pitching_stats(home_lineup)

        mcGame = MonteCarlo(game_obj,away_lineup,home_lineup,away_pitching,home_pitching)
        mcGame.sim_games()





if __name__ == '__main__':
    main()
