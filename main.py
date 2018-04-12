from datetime import datetime
from scrapers.scraper_utils import team_codes
from storage.Game import Game
from simulation.MonteCarlo import MonteCarlo
from converters import winpct_to_ml, over_total_pct, d_to_a, ml_to_winpct
from scrapers.update import update_all
import gsheets_upload
import pandas as pd
import sys
import os

def calc_averages():
    avgs_dict = dict()
    steamer_batters = pd.read_csv(os.path.join('data','steamer',
                                               'steamer_hitters_2018.csv'))
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
    steamer_batters = pd.read_csv(os.path.join('data','steamer',
                                               'steamer_hitters_2018.csv'))
    for i in range(1,10):
        batter_name = lineup.iloc[0][str(i)]

        row = steamer_batters.loc[
                (steamer_batters['firstname'] == batter_name.split(' ',1)[0]) \
                & (steamer_batters['lastname'] == batter_name.split(' ',1)[1])
            ].to_dict('list')
        if len(row['mlbamid']) == 0:
            print(batter_name, "is probably a pitcher, given avg pitcher stats")
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
    steamer_pitchers = pd.read_csv(os.path.join('data','steamer',
                                                'steamer_pitchers_2018.csv'))
    pitcher_name = lineup.iloc[0]['10']
    team_abbrv = team_codes[lineup.iloc[0]['name']].upper()
    if team_abbrv == 'ANA':
        team_abbrv = 'LAA'
    starting_pitcher = steamer_pitchers.loc[
        (steamer_pitchers['firstname'] == pitcher_name.split(' ',1)[0]) & \
        (steamer_pitchers['lastname'] == pitcher_name.split(' ',1)[1]) & \
        (steamer_pitchers['DBTeamId'] == team_abbrv)].to_dict('list')
    relief_pitchers = steamer_pitchers.loc[
        (steamer_pitchers['relief_IP'] >= 10.0) &
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
    park_factors = pd.read_csv(os.path.join('data','park_factors','park_factors.csv'))
    game_outputs = []
    for index, game in games.iterrows():
        game_obj = Game(game['date'],game['time'],game['away'],game['home'])
        away_lineup = lineups.loc[(lineups['key'] == game['key']) & \
                                  (game['away'] == lineups['name'])]
        home_lineup = lineups.loc[(lineups['key'] == game['key']) & \
                                  (game['home'] == lineups['name'])]
        if away_lineup.empty or home_lineup.empty:
            continue

        away_output = dict(team=game['away'],
                           lineup=away_lineup.iloc[0]['lineup_status'])
        home_output = dict(team=game['home'],
                           lineup=home_lineup.iloc[0]['lineup_status'])
        away_lineup_stats = get_batting_stats(away_lineup)
        home_lineup_stats = get_batting_stats(home_lineup)
        away_pitching = get_pitching_stats(away_lineup)
        home_pitching = get_pitching_stats(home_lineup)
        pf = park_factors.loc[park_factors["Team"]==game["home"]].to_dict(orient='records')

        print("Simulating game:",today,game['time'],game['away'],game['home'])
        print("Away lineup is", away_lineup.iloc[0]['lineup_status'],
              "|| Home lineup is", home_lineup.iloc[0]['lineup_status'])
        mcGame = MonteCarlo(game_obj,away_lineup_stats,home_lineup_stats,
                            away_pitching,home_pitching,league_avgs, pf)
        mcGame.sim_games()

        print("Vegas away ML:",round(d_to_a(game['ml_away']),0),
              "|| Vegas home ML:",round(d_to_a(game['ml_home']),0))
        away_output['ml'] = round(d_to_a(game['ml_away']),0)
        home_output['ml'] = round(d_to_a(game['ml_home']),0)

        away_output['ml_proj'] = round(winpct_to_ml(1-(mcGame.home_win_prob*1.04)),0)
        home_output['ml_proj'] = round(winpct_to_ml(mcGame.home_win_prob*1.04),0)
        print('Projected away win pct:',
              round((1-(mcGame.home_win_prob*1.04)) * 100.0, 2),
              'Implied line:', away_output['ml_proj'])
        print('Projected home win pct:',
              round((mcGame.home_win_prob * 1.04) * 100.0, 2),
              'Implied line:', home_output['ml_proj'])

        away_output['ml_value'] = round(100.0 * (1-(mcGame.home_win_prob*1.04) - \
                                   ml_to_winpct(d_to_a(game['ml_away']))), 2)
        home_output['ml_value'] = round(100.0 * (mcGame.home_win_prob*1.04 - \
                                   ml_to_winpct(d_to_a(game['ml_home']))), 2)
        print('Away moneyline value:', round(away_output['ml_value'], 2), '%')
        print('Home moneyline value:', round(home_output['ml_value'], 2), '%')

        print("Vegas away RL:",round(d_to_a(game['rl_away']),0),
            "|| Vegas home RL:",round(d_to_a(game['rl_home']),0))
        away_output['rl'] = round(d_to_a(game['rl_away']),2)
        home_output['rl'] = round(d_to_a(game['rl_home']),2)


        if d_to_a(game['ml_away']) < d_to_a(game['ml_home']):
            away_sign = '-'
            away_rl_win_pct = 1-(mcGame.home_rl_dog_wins/mcGame.number_of_sims * 1.04)
        else:
            away_sign = '+'
            away_rl_win_pct = 1-(mcGame.home_rl_fav_wins/mcGame.number_of_sims * 1.04)

        away_output['rl_proj'] = round(winpct_to_ml(away_rl_win_pct),0)
        away_output['rl_value'] = round((away_rl_win_pct - \
                            ml_to_winpct(d_to_a(game['rl_away']))) * 100, 2)

        if d_to_a(game['ml_away']) >= d_to_a(game['ml_home']):
            home_sign = '-'
            home_rl_win_pct = mcGame.home_rl_fav_wins/mcGame.number_of_sims * 1.04
        else:
            home_sign = '+'
            home_rl_win_pct = mcGame.home_rl_dog_wins/mcGame.number_of_sims * 1.04

        home_output['rl_proj'] = round(winpct_to_ml(home_rl_win_pct),0)
        home_output['rl_value'] = round((home_rl_win_pct - \
                            ml_to_winpct(d_to_a(game['rl_home']))) * 100, 2)
        print('Projected away '+away_sign+'1.5 win pct:', round(away_rl_win_pct * 100, 2),
              'Implied line:', round(away_output['rl_proj'], 1))
        print('Projected home '+home_sign+'1.5 win pct:', round(home_rl_win_pct * 100, 2),
              'Implied line:', round(home_output['rl_proj'], 1))
        print('Away runline value:', round(away_output['rl_value'], 2), '%')
        print('home runline value:', round(home_output['rl_value'], 2), '%')

        print('Vegas total/line:',game['total_line'],round(d_to_a(game['total_odds']),0))
        away_output['total'] = game['total_line']
        home_output['total'] = round(d_to_a(game['total_odds']),0)

        over_prob = over_total_pct(mcGame.comb_histo, game['total_line'])
        away_output['total_proj'] = round(mcGame.avg_total, 2)
        home_output['total_proj'] = round(over_prob * 100.0, 1)

        away_output['total_value'] = round((over_prob - ml_to_winpct(d_to_a(game['total_odds']))) * 100, 2)
        home_output['total_value'] = '--'
        print('Over probability:', round(home_output['total_proj'], 2),
              'Implied line:', round(winpct_to_ml(over_prob), 0))
        print('Over value:', round(away_output['total_value'], 2), '%')

        print("Vegas away F5 ML:",round(d_to_a(game['ml_away_f5']),0),
              "|| Vegas home F5 ML:",round(d_to_a(game['ml_home_f5']),0))
        away_output['ml_f5'] = round(d_to_a(game['ml_away_f5']),0)
        home_output['ml_f5'] = round(d_to_a(game['ml_home_f5']),0)

        away_output['ml_proj_f5'] = round(winpct_to_ml(1-(mcGame.f5_home_win_prob * 1.04)), 0)
        home_output['ml_proj_f5'] = round(winpct_to_ml(mcGame.f5_home_win_prob * 1.04), 0)
        print('Projected away f5 win pct:',
              round((1 - mcGame.f5_home_win_prob * 1.04) * 100.0, 2),
              'Implied line:', round(away_output['ml_proj_f5'],1))
        print('Projected home f5 win pct:',
              round(mcGame.f5_home_win_prob * 1.04 * 100.0, 2),
              'Implied line:', round(home_output['ml_proj_f5'],1))

        away_output['ml_value_f5'] = round((1 - (mcGame.f5_home_win_prob * 1.04) - \
                                ml_to_winpct(d_to_a(game['ml_away_f5']))) * 100, 2)
        home_output['ml_value_f5'] = round(((mcGame.f5_home_win_prob * 1.04) - \
                                ml_to_winpct(d_to_a(game['ml_home_f5']))) * 100, 2)
        print('Away f5 ML value:', away_output['ml_value_f5'], '%')
        print('Home f5 ML value:', home_output['ml_value_f5'], '%')

        if game['rl_away_f5'] != game['rl_away_f5']:
            continue
        print("Vegas away F5 RL:",round(d_to_a(game['rl_away_f5']),0),
              "|| Vegas home F5 RL:",round(d_to_a(game['rl_home_f5']),0))
        away_output['rl_f5'] = round(d_to_a(game['rl_away_f5']),0)
        home_output['rl_f5'] = round(d_to_a(game['rl_home_f5']),0)

        if d_to_a(game['ml_away_f5']) < d_to_a(game['ml_home_f5']):
            away_sign = '-'
            away_win_pct = 1 - (mcGame.f5_home_win_no_tie_prob + mcGame.f5_tie_prob) * 1.04
        else:
            away_sign = '+'
            away_win_pct = 1 - mcGame.f5_home_win_no_tie_prob * 1.04

        away_output['rl_proj_f5'] = round(winpct_to_ml(away_win_pct), 0)
        away_output['rl_value_f5'] = round((away_win_pct - ml_to_winpct(
                                        d_to_a(game['rl_away_f5']))) * 100, 2)

        if d_to_a(game['ml_away_f5']) >= d_to_a(game['ml_home_f5']):
            home_sign = '-'
            home_win_pct = mcGame.f5_home_win_no_tie_prob * 1.04
        else:
            home_sign = '+'
            home_win_pct = (mcGame.f5_home_win_no_tie_prob + mcGame.f5_tie_prob) * 1.04

        home_output['rl_proj_f5'] = round(winpct_to_ml(home_win_pct), 0)
        home_output['rl_value_f5'] = round((home_win_pct - ml_to_winpct(
                                        d_to_a(game['rl_home_f5']))) * 100, 2)
        print('Projected away f5 '+away_sign+'0.5 win pct:',
              round(away_win_pct * 100.0, 2),
              'Implied line:', away_output['rl_proj_f5'])
        print('Projected home f5 '+home_sign+'0.5 win pct:',
              round(home_win_pct * 100.0, 2),
              'Implied line:', home_output['rl_proj_f5'])
        print('Away f5 RL value:', away_output['rl_value_f5'], '%')
        print('Home f5 RL value:', home_output['rl_value_f5'], '%')

        print('Vegas F5 total/line:',
              game['total_line_f5'], d_to_a(game['total_odds_f5']))
        away_output['total_f5'] = game['total_line_f5']
        home_output['total_f5'] = round(d_to_a(game['total_odds_f5']),0)

        f5_over_prob = over_total_pct(mcGame.f5_comb_histo,game['total_line_f5'])
        away_output['total_proj_f5'] = round(mcGame.f5_avg_total,2)
        home_output['total_proj_f5'] = round(f5_over_prob * 100.0,2)

        away_output['total_value_f5'] = round((f5_over_prob - \
                            ml_to_winpct(d_to_a(game['total_odds_f5']))) * 100, 2)
        home_output['total_value_f5'] = '--'
        print('F5 over probability:', round(f5_over_prob * 100.0, 2),
              'Implied line:', round(winpct_to_ml(f5_over_prob), 0))
        print('F5 over value:', away_output['total_value_f5'], '%')

        away_output['sc_in_first']= round(mcGame.scores_in_first/mcGame.number_of_sims*100, 1)
        home_output['sc_in_first']= round(winpct_to_ml(mcGame.scores_in_first/mcGame.number_of_sims),0)

        print('Score in first pct:', away_output['sc_in_first'],
              'Implied line:', home_output['sc_in_first'])

        print('\n')
        game_outputs.append((game['time'], away_output, home_output))
    gsheets_upload.update_spreadsheet(game_outputs)


if __name__ == '__main__':
    update_all()
    main()
