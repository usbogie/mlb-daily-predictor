from datetime import datetime
from scrapers.scraper_utils import team_codes
from storage.Game import Game
from simulation.MonteCarlo import MonteCarlo
from converters import winpct_to_moneyline, over_total_pct, d_to_a, moneyline_to_winpct
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
    avgs_dict['BB'] = steamer_batters['BB'].sum() / float(total_PA)
    avgs_dict['HBP'] = steamer_batters['HBP'].sum() / float(total_PA)
    avgs_dict['K'] = steamer_batters['K'].sum() / float(total_PA)
    return avgs_dict

def get_batting_stats(lineup):
    lineup_stats = []
    avg_pitcher_stats = {'PA': 5277, '1B': 464, '2B': 79, '3B': 7, 'HR': 27,
                         'BB': 162, 'HBP': 16, 'K': 2028}
    steamer_batters = pd.read_csv(os.path.join('data','steamer','steamer_hitters_2018.csv'))
    for i in range(1,10):
        batter_name = lineup.iloc[0][str(i)]
        row = steamer_batters.loc[(steamer_batters['firstname'] == batter_name.split(' ',1)[0]) & \
                                  (steamer_batters['lastname'] == batter_name.split(' ',1)[1])].to_dict('list')
        if len(row['mlbamid']) == 0:
            print(batter_name, "is probably a pitcher, giving him average pitcher stats")
            lineup_stats.append(dict(avg_pitcher_stats))
            continue
        ans = None
        for key, val in row.items():
            if len(val) > 1:
                if ans is None:
                    print("DUPLICATE something is wrong")
                    print(row)
                    ans = input("Which player is actually playing? => ")
                row[key] = val[int(ans)-1]
            else:
                row[key] = val[0]
        lineup_stats.append(row)
    return lineup_stats

def get_pitching_stats(lineup):
    lineup_stats = []
    steamer_pitchers = pd.read_csv(os.path.join('data','steamer','steamer_pitchers_2018.csv'))
    pitcher_name = lineup.iloc[0]['10']
    team_abbrv = team_codes[lineup.iloc[0]['name']].upper()
    if team_abbrv == 'ANA':
        team_abbrv = 'LAA'
    starting_pitcher = steamer_pitchers.loc[(steamer_pitchers['firstname'] == pitcher_name.split(' ',1)[0]) & \
                                  (steamer_pitchers['lastname'] == pitcher_name.split(' ',1)[1]) & \
                                  (steamer_pitchers['DBTeamId'] == team_abbrv)].to_dict('list')
    relief_pitchers = steamer_pitchers.loc[(steamer_pitchers['relief_IP'] >= 10.0) & \
                                           ((steamer_pitchers['DBTeamId'] == team_abbrv))]
    print(pitcher_name)
    for key, val in starting_pitcher.items():
        if len(val) > 1:
            print("DUPLICATE something is wrong")
            sys.exit()
        starting_pitcher[key] = val[0]

    return [starting_pitcher] + list(relief_pitchers.T.to_dict().values())

def main():
    today = datetime.now().strftime('%Y-%m-%d')
    league_avgs = calc_averages()
    games = pd.read_csv(os.path.join('data','lines','today.csv'))
    lineups = pd.read_csv(os.path.join('data','lineups','today.csv'))
    for index, game in games.iterrows():
        game_obj = Game(game['date'],game['time'],game['away'],game['home'])
        away_lineup = lineups.loc[(lineups['key'] == game['key']) & (game['away'] == lineups['name'])]
        home_lineup = lineups.loc[(lineups['key'] == game['key']) & (game['home'] == lineups['name'])]
        if away_lineup.empty or home_lineup.empty:
            continue
        away_lineup_stats = get_batting_stats(away_lineup)
        home_lineup_stats = get_batting_stats(home_lineup)
        away_pitching = get_pitching_stats(away_lineup)
        home_pitching = get_pitching_stats(home_lineup)

        print("Simulating game:", game['date'],game['time'],game['away'],game['home'])
        print("Away lineup is", away_lineup.iloc[0]['lineup_status'], "|| Home lineup is", home_lineup.iloc[0]['lineup_status'])
        mcGame = MonteCarlo(game_obj,away_lineup_stats,home_lineup_stats,away_pitching,home_pitching,league_avgs)
        mcGame.sim_games()
        print("Vegas away ML:",round(d_to_a(game['ml_away']),2),"|| Vegas home ML:",round(d_to_a(game['ml_home']),2))

        print('Projected away win pct:', round((mcGame.away_win_prob - 0.04) * 100.0, 2), 'Implied line:', round(winpct_to_moneyline(mcGame.away_win_prob - 0.04),1))
        print('Projected home win pct:', round((mcGame.home_win_prob + 0.04) * 100.0, 2), 'Implied line:', round(winpct_to_moneyline(mcGame.home_win_prob + 0.04),1))
        print('Away moneyline value:', str(round((mcGame.away_win_prob - 0.04 - moneyline_to_winpct(d_to_a(game['ml_away']))) * 100.0, 2))+'%')
        print('Home moneyline value:', str(round((mcGame.home_win_prob + 0.04 - moneyline_to_winpct(d_to_a(game['ml_home']))) * 100.0, 2))+'%')

        print("Vegas away RL:",round(d_to_a(game['rl_away']),2),"|| Vegas home RL:",round(d_to_a(game['rl_home']),2))
        away_fav_rl_win_prob = mcGame.away_rl_wins / mcGame.number_of_sims
        home_fav_rl_win_prob = mcGame.home_rl_wins / mcGame.number_of_sims
        if d_to_a(game['ml_away']) < d_to_a(game['ml_home']):
            print('Projected away -1.5 win pct:', round((away_fav_rl_win_prob - 0.04) * 100.0, 2), 'Implied line:', round(winpct_to_moneyline(away_fav_rl_win_prob - 0.04), 1))
            print('Away runline value:', str(round((away_fav_rl_win_prob - 0.04 - moneyline_to_winpct(d_to_a(game['rl_away']))) * 100.0, 2))+'%')
        else:
            print('Projected away +1.5 win pct:', round((1-home_fav_rl_win_prob - 0.04) * 100.0, 2), 'Implied line:', round(winpct_to_moneyline(1 - home_fav_rl_win_prob-0.04), 1))
            print('Away runline value:', str(round((1-home_fav_rl_win_prob - 0.04 - moneyline_to_winpct(d_to_a(game['rl_away']))) * 100.0, 2))+'%')

        if d_to_a(game['ml_away']) >= d_to_a(game['ml_home']):
            print('Projected home -1.5 win pct:', round((home_fav_rl_win_prob + 0.04) * 100.0, 2), 'Implied line:', round(winpct_to_moneyline(home_fav_rl_win_prob + 0.04), 1))
            print('Home runline value:', str(round((home_fav_rl_win_prob + 0.04 - moneyline_to_winpct(d_to_a(game['rl_home']))) * 100.0, 2))+'%')
        else:
            print('Projected home +1.5 win pct:', round((1 - away_fav_rl_win_prob + 0.04) * 100.0, 2), 'Implied line:', round(winpct_to_moneyline(1 - away_fav_rl_win_prob + 0.04), 1))
            print('home runline value:', str(round((1 - away_fav_rl_win_prob + 0.04 - moneyline_to_winpct(d_to_a(game['rl_home']))) * 100.0, 2))+'%')
            
        print('Vegas total (over line):', game['total_line'], d_to_a(game['total_odds']))
        over_prob = over_total_pct(mcGame.comb_histo,game['total_line'])
        print('Over probability:', round(over_prob * 100.0, 2), 'Implied line:', round(winpct_to_moneyline(over_prob), 1))
        print('Over value:', str(round((over_prob - moneyline_to_winpct(d_to_a(game['total_odds']))) * 100.0, 2))+'%')

        print('Score in first pct:', round(mcGame.scores_in_first/mcGame.number_of_sims, 4), 'Implied line:', winpct_to_moneyline(mcGame.scores_in_first/mcGame.number_of_sims))

        print("Vegas away F5 ML:",round(d_to_a(game['ml_away_f5']),2),"|| Vegas home F5 ML:",round(d_to_a(game['ml_home_f5']),2))
        print('Projected away f5 win pct:', round((mcGame.f5_away_win_prob - 0.04) * 100.0, 2), 'Implied line:', round(winpct_to_moneyline(mcGame.f5_away_win_prob - 0.04),1))
        print('Projected home f5 win pct:', round((mcGame.f5_home_win_prob + 0.04) * 100.0, 2), 'Implied line:', round(winpct_to_moneyline(mcGame.home_win_prob + 0.04),1))
        print('Away f5 moneyline value:', str(round((mcGame.f5_away_win_prob - 0.04 - moneyline_to_winpct(d_to_a(game['ml_away_f5']))) * 100.0, 2))+'%')
        print('Home f5 moneyline value:', str(round((mcGame.f5_home_win_prob + 0.04 - moneyline_to_winpct(d_to_a(game['ml_home_f5']))) * 100.0, 2))+'%')

        print("Vegas away F5 RL:",round(d_to_a(game['rl_away_f5']),2),"|| Vegas home F5 RL:",round(d_to_a(game['rl_home_f5']),2))
        if d_to_a(game['ml_away_f5']) < d_to_a(game['ml_home_f5']):
            print('Projected away f5 -0.5 win pct:', round((mcGame.f5_away_win_no_tie_prob - 0.04) * 100.0, 2), 'Implied line:', round(winpct_to_moneyline(mcGame.f5_away_win_no_tie_prob - 0.04), 1))
            print('Away f5 runline value:', str(round((mcGame.f5_away_win_no_tie_prob - 0.04 - moneyline_to_winpct(d_to_a(game['rl_away_f5']))) * 100.0, 2))+'%')
        else:
            print('Projected away f5 +0.5 win pct:', round((1-mcGame.f5_home_win_no_tie_prob - 0.04) * 100.0, 2), 'Implied line:', round(winpct_to_moneyline(1 - mcGame.f5_home_win_no_tie_prob-0.04), 1))
            print('Away f5 runline value:', str(round((1-mcGame.f5_home_win_no_tie_prob - 0.04 - moneyline_to_winpct(d_to_a(game['rl_away_f5']))) * 100.0, 2))+'%')

        if d_to_a(game['ml_away_f5']) >= d_to_a(game['ml_home_f5']):
            print('Projected home f5 -0.5 win pct:', round((mcGame.f5_home_win_no_tie_prob + 0.04) * 100.0, 2), 'Implied line:', round(winpct_to_moneyline(mcGame.f5_home_win_no_tie_prob + 0.04), 1))
            print('Home f5 runline value:', str(round((mcGame.f5_home_win_no_tie_prob + 0.04 - moneyline_to_winpct(d_to_a(game['rl_home_f5']))) * 100.0, 2))+'%')
        else:
            print('Projected home f5 +0.5 win pct:', round((1 - mcGame.f5_away_win_no_tie_prob + 0.04) * 100.0, 2), 'Implied line:', round(winpct_to_moneyline(1 - mcGame.f5_away_win_no_tie_prob + 0.04), 1))
            print('home f5 runline value:', str(round((1 - mcGame.f5_away_win_no_tie_prob + 0.04 - moneyline_to_winpct(d_to_a(game['rl_home_f5']))) * 100.0, 2))+'%')

        print('Vegas F5 total (over line):', game['total_line_f5'], d_to_a(game['total_odds_f5']))
        f5_over_prob = over_total_pct(mcGame.f5_comb_histo,game['total_line_f5'])
        print('F5 over probability:', round(f5_over_prob * 100.0, 2), 'Implied line:', round(winpct_to_moneyline(f5_over_prob), 1))
        print('F5 over value:', str(round((f5_over_prob - moneyline_to_winpct(d_to_a(game['total_odds_f5']))) * 100.0, 2))+'%')
        print('\n')


if __name__ == '__main__':
    main()
