from datetime import datetime
from scrapers.scraper_utils import team_codes, get_days_in_season
from storage.Game import Game
from simulation.MonteCarlo import MonteCarlo
from utils.converters import winpct_to_ml, over_total_pct, d_to_a, ml_to_winpct, third_kelly_calculator, amount_won
from lineups.lineups import get_batting_stats, get_pitching_stats
from lineups.matchups import generate_matchups
from scrapers.update import update_all
from update_projections import batter_dict, pitcher_dict
import gsheets_upload
import pandas as pd
import random
import json
import sys
import os
import argparse

year = 2018

batter_projections = pd.read_csv(os.path.join('data','projections','hitters_{}.csv'.format(year)))
pitcher_projections = pd.read_csv(os.path.join('data','projections','pitchers_{}.csv'.format(year)))

steamer_batters = pd.read_csv(os.path.join('data','steamer', 'steamer_hitters_{}_split.csv'.format(year)))
steamer_batters['fullname'] = steamer_batters[['firstname', 'lastname']].apply(lambda x: ' '.join(x), axis=1)

steamer_pitchers = pd.read_csv(os.path.join('data','steamer','steamer_pitchers_{}_split.csv'.format(year)))
steamer_pitchers['fullname'] = steamer_pitchers[['firstname', 'lastname']].apply(lambda x: ' '.join(x), axis=1)
steamer_starters = pd.read_csv(os.path.join('data','steamer','steamer_pitchers_{}.csv'.format(year)))

bullpens = pd.read_csv(os.path.join('data','lineups','bullpens_{}.csv'.format(year)))
manifest = pd.read_csv(os.path.join('data','master.csv'))

with open(os.path.join('data','relievers.json')) as f:
    all_relievers = json.load(f)

def main():
    bankroll = 1000
    today = datetime.now().strftime('%Y-%m-%d')
    games = pd.read_csv(os.path.join('data','lines','today.csv'))
    lineups = pd.read_csv(os.path.join('data','lineups','today.csv'))
    park_factors = pd.read_csv(os.path.join('data','park_factors_handedness.csv'))
    game_outputs = []
    for index, game in games.iterrows():
        print('\n')
        game_obj = Game(game['date'],game['time'],game['away'],game['home'])
        print("Simulating game:",today,game['time'],game['away'],game['home'])
        away_lineup = lineups[(lineups['key'] == game['key']) & (game['away'] == lineups['name'])].to_dict('records')[0]
        home_lineup = lineups[(lineups['key'] == game['key']) & (game['home'] == lineups['name'])].to_dict('records')[0]

        away_output = dict(team=game['away'], lineup=away_lineup['lineup_status'])
        home_output = dict(team=game['home'], lineup=home_lineup['lineup_status'])
        away_lineup_stats = get_batting_stats(manifest, batter_projections, steamer_batters, away_lineup, game['date'])
        home_lineup_stats = get_batting_stats(manifest, batter_projections, steamer_batters, home_lineup, game['date'])
        away_pitching = get_pitching_stats(manifest, pitcher_projections, all_relievers, steamer_pitchers, steamer_starters, away_lineup, game['date'], test=False)
        home_pitching = get_pitching_stats(manifest, pitcher_projections, all_relievers, steamer_pitchers, steamer_starters, home_lineup, game['date'], test=False)
        if not away_pitching or not home_pitching:
            print("SOMETHING WRONG MAYBE CHECK IT OUT")
            continue
        pf = park_factors[park_factors["Team"]==game["home"]].to_dict(orient='records')

        all_matchups = generate_matchups(pf,steamer_batters, home_pitching, away_pitching, home_lineup_stats, away_lineup_stats)
        print("Away lineup is", away_lineup['lineup_status'],"|| Home lineup is", home_lineup['lineup_status'])
        mcGame = MonteCarlo(game_obj,away_lineup_stats,home_lineup_stats,away_pitching,home_pitching, all_matchups)
        mcGame.sim_games()

        print("Vegas away ML:",round(d_to_a(game['ml_away']),0),
              "|| Vegas home ML:",round(d_to_a(game['ml_home']),0))
        away_output['ml'] = round(d_to_a(game['ml_away']),0)
        home_output['ml'] = round(d_to_a(game['ml_home']),0)

        away_output['ml_proj'] = round(winpct_to_ml(1-(mcGame.home_win_prob*1.08)),0)
        home_output['ml_proj'] = round(winpct_to_ml(mcGame.home_win_prob*1.08),0)
        print('Projected away win pct:',
              round((1-(mcGame.home_win_prob*1.08)) * 100.0, 2),
              'Implied line:', away_output['ml_proj'])
        print('Projected home win pct:',
              round((mcGame.home_win_prob * 1.08) * 100.0, 2),
              'Implied line:', home_output['ml_proj'])

        away_output['ml_value'] = round(100.0 * (1-(mcGame.home_win_prob*1.08) - ml_to_winpct(d_to_a(game['ml_away']))), 2)
        home_output['ml_value'] = round(100.0 * (mcGame.home_win_prob*1.08 - ml_to_winpct(d_to_a(game['ml_home']))), 2)
        print('Away moneyline value:', round(away_output['ml_value'], 2), '%')
        print('Home moneyline value:', round(home_output['ml_value'], 2), '%')
        kelly_away = third_kelly_calculator(game['ml_away'], 1-(mcGame.home_win_prob*1.08))
        kelly_home = third_kelly_calculator(game['ml_home'], mcGame.home_win_prob*1.08)
        away_output['kelly_risk'] = '${}'.format(round(bankroll*kelly_away/100.0,0))
        home_output['kelly_risk'] = '${}'.format(round(bankroll*kelly_home/100.0,0))
        print('Kelly br%: away {} ${}'.format(round(kelly_away,1),round(bankroll*kelly_away/100.0,0)))
        print('Kelly br%: home {} ${}'.format(round(kelly_home,1),round(bankroll*kelly_home/100.0,0)))

        if 'rl_away' in game and game['rl_away'] == game['rl_away']:
            print("Vegas away RL:",round(d_to_a(game['rl_away']),0),
                "|| Vegas home RL:",round(d_to_a(game['rl_home']),0))
            away_output['rl'] = round(d_to_a(game['rl_away']),0)
            home_output['rl'] = round(d_to_a(game['rl_home']),0)

            if d_to_a(game['ml_away']) < -100 and d_to_a(game['ml_home']) < -100:
                rl_fav = 'away' if d_to_a(game['rl_home']) < 100 else 'home'
            else:
                rl_fav = 'away' if d_to_a(game['ml_away']) < d_to_a(game['ml_home']) else 'home'

            if rl_fav == 'away':
                away_sign = '-'
                away_rl_win_pct = 1-(mcGame.home_rl_dog_wins/mcGame.number_of_sims * 1.08)
            else:
                away_sign = '+'
                away_rl_win_pct = 1-(mcGame.home_rl_fav_wins/mcGame.number_of_sims * 1.08)

            away_output['rl_proj'] = round(winpct_to_ml(away_rl_win_pct),0)
            away_output['rl_value'] = round((away_rl_win_pct - \
                                ml_to_winpct(d_to_a(game['rl_away']))) * 100, 2)

            if rl_fav == 'home':
                home_sign = '-'
                home_rl_win_pct = mcGame.home_rl_fav_wins/mcGame.number_of_sims * 1.08
            else:
                home_sign = '+'
                home_rl_win_pct = mcGame.home_rl_dog_wins/mcGame.number_of_sims * 1.08

            home_output['rl_proj'] = round(winpct_to_ml(home_rl_win_pct),0)
            home_output['rl_value'] = round((home_rl_win_pct - \
                                ml_to_winpct(d_to_a(game['rl_home']))) * 100, 2)
            print('Projected away '+away_sign+'1.5 win pct:', round(away_rl_win_pct * 100, 2),
                  'Implied line:', round(away_output['rl_proj'], 1))
            print('Projected home '+home_sign+'1.5 win pct:', round(home_rl_win_pct * 100, 2),
                  'Implied line:', round(home_output['rl_proj'], 1))
            print('Away runline value:', round(away_output['rl_value'], 2), '%')
            print('home runline value:', round(home_output['rl_value'], 2), '%')
        else:
            away_output['rl'] = "NA"
            home_output['rl'] = "NA"
            away_output['rl_proj'] = "NA"
            home_output['rl_proj'] = "NA"
            away_output['rl_value'] = "NA"
            home_output['rl_value'] = "NA"

        if 'total_line' in game and game['total_line'] == game['total_line']:
            print('Vegas over:',game['total_line'],round(d_to_a(game['over_odds']),0))
            away_output['total'] = str(game['total_line'])+" "+str(round(d_to_a(game['over_odds']),0))
            home_output['total'] = str(game['total_line'])+" "+str(round(d_to_a(game['under_odds']),0))

            over_prob = over_total_pct(mcGame.comb_histo, game['total_line'])
            # away_output['total_proj'] = round(mcGame.avg_total, 2)
            # home_output['total_proj'] = str(round(over_prob * 100.0, 1))+'%'

            away_output['total_value'] = round((over_prob - ml_to_winpct(d_to_a(game['over_odds']))) * 100, 2)
            home_output['total_value'] = round((1 - over_prob - ml_to_winpct(d_to_a(game['under_odds']))) * 100, 2)
            print('Over probability:', round(over_prob * 100.0, 2),
                  'Implied line:', round(winpct_to_ml(over_prob), 0))
            print('Under probability:', round((1-over_prob) * 100.0, 2),
                  'Implied line:', round(winpct_to_ml(1-over_prob), 0))
            print('Over value:', away_output['total_value'], '%')
            print('Under value:', home_output['total_value'], '%')
        else:
            away_output['total'] = "NA"
            home_output['total'] = "NA"
            # away_output['total_proj'] = "NA"
            # home_output['total_proj'] = "NA"
            away_output['total_value'] = "NA"
            home_output['total_value'] = "NA"

        if 'ml_away_f5' in game and 'ml_away_f5' in game and game['ml_away_f5'] == game['ml_away_f5']:
            print("Vegas away F5 ML:",round(d_to_a(game['ml_away_f5']),0),
                  "|| Vegas home F5 ML:",round(d_to_a(game['ml_home_f5']),0))
            away_output['ml_f5'] = round(d_to_a(game['ml_away_f5']),0)
            home_output['ml_f5'] = round(d_to_a(game['ml_home_f5']),0)

            away_output['ml_proj_f5'] = round(winpct_to_ml(1-(mcGame.f5_home_win_prob * 1.08)), 0)
            home_output['ml_proj_f5'] = round(winpct_to_ml(mcGame.f5_home_win_prob * 1.08), 0)
            print('Projected away f5 win pct:',
                  round((1 - mcGame.f5_home_win_prob * 1.08) * 100.0, 2),
                  'Implied line:', round(away_output['ml_proj_f5'],1))
            print('Projected home f5 win pct:',
                  round(mcGame.f5_home_win_prob * 1.08 * 100.0, 2),
                  'Implied line:', round(home_output['ml_proj_f5'],1))

            away_output['ml_value_f5'] = round((1 - (mcGame.f5_home_win_prob * 1.08) - \
                                    ml_to_winpct(d_to_a(game['ml_away_f5']))) * 100, 2)
            home_output['ml_value_f5'] = round(((mcGame.f5_home_win_prob * 1.08) - \
                                    ml_to_winpct(d_to_a(game['ml_home_f5']))) * 100, 2)
            print('Away f5 ML value:', away_output['ml_value_f5'], '%')
            print('Home f5 ML value:', home_output['ml_value_f5'], '%')
        else:
            away_output['ml_f5'] = "NA"
            home_output['ml_f5'] = "NA"
            away_output['ml_proj_f5'] = "NA"
            home_output['ml_proj_f5'] = "NA"
            away_output['ml_value_f5'] = "NA"
            home_output['ml_value_f5'] = "NA"

        if 'rl_away_f5' in game and game['rl_away_f5'] == game['rl_away_f5']:
            print("Vegas away F5 RL:",round(d_to_a(game['rl_away_f5']),0),
                  "|| Vegas home F5 RL:",round(d_to_a(game['rl_home_f5']),0))
            away_output['rl_f5'] = round(d_to_a(game['rl_away_f5']),0)
            home_output['rl_f5'] = round(d_to_a(game['rl_home_f5']),0)

            if d_to_a(game['ml_away_f5']) < d_to_a(game['ml_home_f5']):
                away_sign = '-'
                away_win_pct = 1 - (mcGame.f5_home_win_no_tie_prob + mcGame.f5_tie_prob) * 1.08
            else:
                away_sign = '+'
                away_win_pct = 1 - mcGame.f5_home_win_no_tie_prob * 1.08

            away_output['rl_proj_f5'] = round(winpct_to_ml(away_win_pct), 0)
            away_output['rl_value_f5'] = round((away_win_pct - ml_to_winpct(
                                            d_to_a(game['rl_away_f5']))) * 100, 2)

            if d_to_a(game['ml_away_f5']) >= d_to_a(game['ml_home_f5']):
                home_sign = '-'
                home_win_pct = mcGame.f5_home_win_no_tie_prob * 1.08
            else:
                home_sign = '+'
                home_win_pct = (mcGame.f5_home_win_no_tie_prob + mcGame.f5_tie_prob) * 1.08

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
        else:
            away_output['rl_f5'] = "NA"
            home_output['rl_f5'] = "NA"
            away_output['rl_proj_f5'] = "NA"
            home_output['rl_proj_f5'] = "NA"
            away_output['rl_value_f5'] = "NA"
            home_output['rl_value_f5'] = "NA"

        if 'total_line_f5' in game and game['total_line_f5'] == game['total_line_f5'] and game['total_line_f5'] < 100:
            print('Vegas F5 over total:',
                  game['total_line_f5'], round(d_to_a(game['over_odds_f5']),0))
            away_output['total_f5'] = str(game['total_line_f5'])+" "+str(round(d_to_a(game['over_odds_f5']),0))
            home_output['total_f5'] = str(game['total_line_f5'])+" "+str(round(d_to_a(game['under_odds_f5']),0))

            f5_over_prob = over_total_pct(mcGame.f5_comb_histo,game['total_line_f5'])
            # away_output['total_proj_f5'] = round(mcGame.f5_avg_total,2)
            # home_output['total_proj_f5'] = str(round(f5_over_prob * 100.0, 1))+'%'

            away_output['total_value_f5'] = round((f5_over_prob - \
                                ml_to_winpct(d_to_a(game['over_odds_f5']))) * 100, 2)
            home_output['total_value_f5'] = round((1 - f5_over_prob - \
                                ml_to_winpct(d_to_a(game['under_odds_f5']))) * 100, 2)
            print('F5 over probability:', round(f5_over_prob * 100.0, 2),
                  'Implied line:', round(winpct_to_ml(f5_over_prob), 0))
            print('F5 under probability:', round((1-f5_over_prob) * 100.0, 2),
                  'Implied line:', round(winpct_to_ml(1-f5_over_prob), 0))
            print('F5 over value:', away_output['total_value_f5'], '%')
            print('F5 under value:', home_output['total_value_f5'], '%')
        else:
            away_output['total_f5'] = "NA"
            home_output['total_f5'] = "NA"
            # away_output['total_proj_f5'] = "NA"
            # home_output['total_proj_f5'] = "NA"
            away_output['total_value_f5'] = "NA"
            home_output['total_value_f5'] = "NA"

        away_output['sc_in_first']= round(mcGame.scores_in_first/mcGame.number_of_sims*100, 1)
        home_output['sc_in_first']= round(winpct_to_ml(mcGame.scores_in_first/mcGame.number_of_sims),0)

        print('Score in first pct:', away_output['sc_in_first'],
              'Implied line:', home_output['sc_in_first'])

        game_outputs.append((game['time'], away_output, home_output))
    gsheets_upload.update_spreadsheet(game_outputs)

    manifest.set_index('mlb_id').to_csv(os.path.join('data','master.csv'))

def test_year(year):
    bankroll = 1000
    days = get_days_in_season(year)
    games = pd.read_csv(os.path.join('data','games','games_{}.csv'.format(year)))
    lines = pd.read_csv(os.path.join('data','lines','lines_{}.csv'.format(year)))
    lineups = pd.read_csv(os.path.join('data','lineups','lineups_{}.csv'.format(year)))
    park_factors = pd.read_csv(os.path.join('data','park_factors_handedness.csv'))

    all_results = []
    all_net = []
    acc = 0
    risk_acc = 0
    for day in days:
        slate = games[games['date'] == day]
        day_results = []
        for index, game in slate.iterrows():
            game_obj = Game(game['date'],'12:05p',game['away'],game['home'])
            away_lineup = lineups[(lineups['key'] == game['key']) & (game['away'] == lineups['name'])].to_dict('records')[0]
            home_lineup = lineups[(lineups['key'] == game['key']) & (game['home'] == lineups['name'])].to_dict('records')[0]
            game_odds = lines[lines['key'] == game['key']]

            if away_lineup['10_name'] in starters_to_ignore[year] or home_lineup['10_name'] in starters_to_ignore[year]:
                print('Starter {} has no projections. Continue'.format(away_lineup['10_name']))
                print('Starter {} has no projections. Continue\n'.format(home_lineup['10_name']))
                continue

            away_lineup_stats = get_batting_stats(away_lineup, game['date'])
            home_lineup_stats = get_batting_stats(home_lineup, game['date'])
            away_pitching = get_pitching_stats(away_lineup, game['date'], test=True)
            home_pitching = get_pitching_stats(home_lineup, game['date'], test=True)
            if not away_pitching or not home_pitching:
                print("SOMETHING WRONG MAYBE CHECK IT OUT")
                ans = input('HELLO is this OKAY to continue?')
                continue
            pf = park_factors[park_factors["Team"]==game["home"]].to_dict(orient='records')

            print("Simulating game:",day,game['away'],'vs',game['home'])
            all_matchups = generate_matchups(pf, home_pitching, away_pitching, home_lineup_stats, away_lineup_stats)
            mcGame = MonteCarlo(game_obj,away_lineup_stats,home_lineup_stats,away_pitching,home_pitching,all_matchups)
            try:
                mcGame.sim_games(test=True)
            except:
                print("Issue, attempting SIM again")
                mcGame.sim_games(test=True)

            away_win_pct = 1-(mcGame.home_win_prob*1.08)
            home_win_pct = mcGame.home_win_prob*1.08
            if game_odds.empty:
                print('home/away odds mismatch. continue\n')
                continue
            result = dict(
                away = game['away'],
                home = game['home'],
                away_ml = round(d_to_a(game_odds.iloc[0]['ml_away']),0),
                home_ml = round(d_to_a(game_odds.iloc[0]['ml_home']),0),
                away_ml_proj = round(winpct_to_ml(away_win_pct),0),
                home_ml_proj = round(winpct_to_ml(home_win_pct),0)
            )

            value_away = round(100.0 * (away_win_pct - ml_to_winpct(result['away_ml'])), 2)
            value_home = round(100.0 * (home_win_pct - ml_to_winpct(result['home_ml'])), 2)

            kelly_away = third_kelly_calculator(game_odds.iloc[0]['ml_away'], away_win_pct) if value_away >= 2.0 else 0
            kelly_home = third_kelly_calculator(game_odds.iloc[0]['ml_home'], home_win_pct) if value_home >= 2.0 else 0

            if kelly_away > 0:
                result['bet_on'] = result['away']
                result['bet_against'] = result['home']
                result['bet_on_pitcher'] = away_lineup['10_name']
                result['bet_against_pitcher'] = home_lineup['10_name']
                result['k_risk'] = round(bankroll*kelly_away/100.0,0)
                result['value'] = round(100.0 * (away_win_pct - ml_to_winpct(result['away_ml'])), 2)
            elif kelly_home > 0:
                result['bet_on'] = result['home']
                result['bet_against'] = result['away']
                result['bet_on_pitcher'] = home_lineup['10_name']
                result['bet_against_pitcher'] = away_lineup['10_name']
                result['k_risk'] = round(bankroll*kelly_home/100.0,0)
                result['value'] = round(100.0 * (home_win_pct - ml_to_winpct(result['home_ml'])), 2)
            else:
                result['bet_on'] = 'no bet'
                result['bet_against'] = 'no bet'
                result['bet_on_pitcher'] = 'no bet'
                result['bet_against_pitcher'] = 'no bet'
                result['k_risk'] = 0
                result['value'] = 0

            result['net'] = 0
            if game['away_score'] > game['home_score']:
                if result['bet_on'] == result['away']:
                    result['net'] = amount_won(result['k_risk'], game_odds.iloc[0]['ml_away'])
                elif result['bet_on'] == result['home']:
                    result['net'] = result['k_risk'] * -1
            if game['home_score'] > game['away_score']:
                if result['bet_on'] == result['home']:
                    result['net'] = amount_won(result['k_risk'], game_odds.iloc[0]['ml_home'])
                elif result['bet_on'] == result['away']:
                    result['net'] = result['k_risk'] * -1


            day_results.append(result)
            print(result['bet_on'], result['k_risk'], result['net'])
        day_risk = 0
        day_net = 0
        for result in day_results:
            day_risk = day_risk + result['k_risk']
            day_net = day_net + result['net']
        risk_acc = risk_acc + day_risk
        acc = acc + day_net
        print(day,'-- total risk:',day_risk,'-- total net:',day_net,'-- acc:',acc)
        print('ROI to date', acc/risk_acc*100)
        day_summary = dict()
        day_summary['date'] = day
        day_summary['risk'] = day_risk
        day_summary['net'] = day_net
        day_summary['acc'] = acc
        all_results.extend(day_results)
        all_net.append(day_summary)

    total_risk = sum([g['k_risk'] for g in all_results])
    total_win = sum([g['net'] for g in all_results])

    print('ROI is', total_win/total_risk*100.0)

    import matplotlib.pyplot as plt

    plt.bar(range(len(all_net)), [day['acc'] for day in all_net])
    ticks = []
    for day in all_net:
        date = day['date']
        if int(date.split('-')[2]) % 5 == 0:
            ticks.append(date[5:])
        else:
            ticks.append('')
    plt.xticks(range(len(all_net)), tuple(ticks))
    plt.show()

    with open(os.path.join('data','results','results_{}.json'.format(year)), 'r+') as f:
        f.truncate()
        json.dump(all_results, f)

    with open(os.path.join('data','results','profits_{}.json'.format(year)), 'r+') as f:
        f.truncate()
        json.dump(all_net, f)

    manifest.set_index('mlb_id').to_csv(os.path.join('data','master.csv'))


if __name__ == '__main__':
    # if you `python3 main.py gr`, program will update relievers, otherwise as normal
    gr = False
    test = False
    if len(sys.argv) > 1:
        print(sys.argv[1])
        gr = sys.argv[1] == 'gr'
        test = sys.argv[1] == 'test'
    if test:
        print('testing')
        test_year(year)
    else:
        update_all(gr)
        main()
