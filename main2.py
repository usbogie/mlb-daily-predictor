import pandas as pd
import gsheets_upload
import json
import sys
import os
from scrapers.scraper_utils import team_codes, get_days_in_season, team_leagues
from storage.Game import Game
from utils.converters import winpct_to_ml, over_total_pct, d_to_a, ml_to_winpct, third_kelly_calculator, amount_won
from utils import get_baserunning_runs, get_batting_runs, get_fielding_runs, get_pitching_runs

year = 2016

starters_to_ignore = {2016: [],
                      2017: [],
                      2018: ['Jonny Venters']}

def test_year(year):
    bankroll = 1000
    days = get_days_in_season(year)
    games = pd.read_csv(os.path.join('data','games','games_{}.csv'.format(year)))
    lines = pd.read_csv(os.path.join('data','lines','lines_{}.csv'.format(year)))
    lineups = pd.read_csv(os.path.join('data','lineups','lineups_{}.csv'.format(year)))
    manifest = pd.read_csv(os.path.join('data','master.csv'))
    batter_projections = pd.read_csv(os.path.join('data','projections','batter_proj_{}.csv'.format(year)))
    pitcher_projections = pd.read_csv(os.path.join('data','projections','pitcher_proj_{}.csv'.format(year)))
    steamer_batters = pd.read_csv(os.path.join('data','steamer', 'steamer_hitters_{}_split.csv'.format(year)))
    steamer_batters['fullname'] = steamer_batters[['firstname', 'lastname']].apply(lambda x: ' '.join(x), axis=1)
    # steamer_pitchers = pd.read_csv(os.path.join('data','steamer','steamer_pitchers_{}_split.csv'.format(year)))
    # steamer_pitchers['fullname'] = steamer_pitchers[['firstname', 'lastname']].apply(lambda x: ' '.join(x), axis=1)

    all_results = []
    all_net = []
    acc = 0
    risk_acc = 0
    my_acc = 0
    vegas_acc = 0
    for day in days:
        slate = games[games['date'] == day]
        day_results = []
        for index, game in slate.iterrows():
            print('')
            try:
                away_lineup = lineups[(lineups['key'] == game['key']) & (game['away'] == lineups['name'])].to_dict('records')[0]
                home_lineup = lineups[(lineups['key'] == game['key']) & (game['home'] == lineups['name'])].to_dict('records')[0]
            except:
                print('mismatch of game/lineup keys for', game['key'], 'continuing')
                continue

            game_obj = Game(game['date'],'12:05p',game['away'],game['home'], 0)

            if away_lineup['10_name'] in starters_to_ignore[year] or home_lineup['10_name'] in starters_to_ignore[year]:
                print('Starter {} has no projections. Continue'.format(away_lineup['10_name']))
                print('Starter {} has no projections. Continue\n'.format(home_lineup['10_name']))
                continue

            try:
                game_odds = lines[lines['key'] == game['key']].to_dict('records')[0]
            except:
                print('something wrong with game odds')
                continue

            print(day,game['away'],'vs',game['home'])

            away_batting_runs = get_batting_runs.calculate(away_lineup, game['date'], manifest, batter_projections)
            home_batting_runs = get_batting_runs.calculate(home_lineup, game['date'], manifest, batter_projections)
            away_pitching_runs = get_pitching_runs.calculate(away_lineup, game['date'], manifest, pitcher_projections)
            print('vs', end=" ")
            home_pitching_runs = get_pitching_runs.calculate(home_lineup, game['date'], manifest, pitcher_projections)
            print()
            print(game['away_score'], '-', game['home_score'])
            if not away_batting_runs or not home_batting_runs or not away_pitching_runs or not home_pitching_runs:
                print("Could not find ^, continue")
                continue

            dh = team_leagues[team_codes[game['home']]] == 'AL'

            away_player_ids = [manifest[manifest['fantasy_labs'] == away_lineup[str(x)+'_id']].iloc[0]['mlb_id']
                               for x in range(1,10)]
            home_player_ids = [manifest[manifest['fantasy_labs'] == home_lineup[str(x)+'_id']].iloc[0]['mlb_id']
                               for x in range(1,10)]

            away_pitcher_id = manifest[manifest['fantasy_labs'] == away_lineup['10_id']].iloc[0]['mlb_id']
            home_pitcher_id = manifest[manifest['fantasy_labs'] == home_lineup['10_id']].iloc[0]['mlb_id']

            away_fielding_runs = get_fielding_runs.calculate(dh, away_pitcher_id, away_player_ids, steamer_batters) / 3
            home_fielding_runs = get_fielding_runs.calculate(dh, home_pitcher_id, home_player_ids, steamer_batters) / 3

            away_baserunning_runs = get_baserunning_runs.calculate(away_lineup, steamer_batters, manifest)
            home_baserunning_runs = get_baserunning_runs.calculate(home_lineup, steamer_batters, manifest)

            # print("Away")
            # print("Batting: {}; BaseRunning: {};\nPitching: {}; Fielding: {};"
            #       .format(away_batting_runs, away_baserunning_runs,
            #               away_pitching_runs, away_fielding_runs))
            # print("Home")
            # print("Batting: {}; BaseRunning: {};\nPitching: {}; Fielding: {};"
            #       .format(home_batting_runs, home_baserunning_runs,
            #               home_pitching_runs, home_fielding_runs))

            away_RS = away_batting_runs + away_baserunning_runs
            away_RA = away_pitching_runs - away_fielding_runs
            away_x = ((away_RS + away_RA) / 162)**.287
            away_season_win_pct = (away_RS**away_x) / (away_RS**away_x + away_RA**away_x)

            home_RS = home_batting_runs + home_baserunning_runs
            home_RA = home_pitching_runs - home_fielding_runs
            home_x = ((home_RS + home_RA) / 162)**.287
            home_season_win_pct = (home_RS**home_x) / (home_RS**home_x + home_RA**home_x)

            home_game_win_pct = (home_season_win_pct \
                                    - (home_season_win_pct * away_season_win_pct)) \
                                / (home_season_win_pct + away_season_win_pct \
                                    - (2 * away_season_win_pct * home_season_win_pct))

            home_win_pct_HFA = home_game_win_pct * 1.08
            # print(home_win_pct_HFA)

            result = dict(
                away = game['away'],
                home = game['home'],
                away_ml = d_to_a(game_odds['ml_away']),
                home_ml = d_to_a(game_odds['ml_home']),
                away_ml_proj = winpct_to_ml(1 - home_win_pct_HFA),
                home_ml_proj = winpct_to_ml(home_win_pct_HFA),
            )

            value = lambda pct, odds: round(100 * pct - ml_to_winpct(odds),1)


            value_away = value(1 - home_win_pct_HFA, game_odds['ml_away'])
            value_home = value(home_win_pct_HFA, game_odds['ml_home'])

            kelly_away = third_kelly_calculator(game_odds['ml_away'], 1 - home_win_pct_HFA) if value_away >= 0 else 0
            kelly_home = third_kelly_calculator(game_odds['ml_home'], home_win_pct_HFA) if value_home >= 0 else 0

            if kelly_away > 0:
                result['bet_on'] = result['away']
                result['bet_against'] = result['home']
                result['bet_on_pitcher'] = away_lineup['10_name']
                result['bet_against_pitcher'] = home_lineup['10_name']
                result['k_risk'] = int(bankroll*kelly_away/100)
                result['side_value'] = value_away
            elif kelly_home > 0:
                result['bet_on'] = result['home']
                result['bet_against'] = result['away']
                result['bet_on_pitcher'] = home_lineup['10_name']
                result['bet_against_pitcher'] = away_lineup['10_name']
                result['k_risk'] = int(bankroll*kelly_home/100)
                result['side_value'] = value_home
            else:
                result['bet_on'] = 'no bet'
                result['bet_against'] = 'no bet'
                result['bet_on_pitcher'] = 'no bet'
                result['bet_against_pitcher'] = 'no bet'
                result['k_risk'] = 0
                result['side_value'] = 0
                result['line'] = 0

            result['net'] = 0
            if game['away_score'] > game['home_score']:
                if result['bet_on'] == result['away']:
                    result['net'] = amount_won(result['k_risk'], game_odds['ml_away'])
                    result['line'] = d_to_a(game_odds['ml_away'])
                elif result['bet_on'] == result['home']:
                    result['net'] = result['k_risk'] * -1
                    result['line'] = d_to_a(game_odds['ml_home'])
                my_acc = my_acc + 1 - home_win_pct_HFA
                vegas_acc = vegas_acc + ml_to_winpct(game_odds['ml_away'])
            elif game['home_score'] > game['away_score']:
                if result['bet_on'] == result['home']:
                    result['net'] = amount_won(result['k_risk'], game_odds['ml_home'])
                    result['line'] = d_to_a(game_odds['ml_home'])
                elif result['bet_on'] == result['away']:
                    result['net'] = result['k_risk'] * -1
                    result['line'] = d_to_a(game_odds['ml_away'])
                my_acc = my_acc + home_win_pct_HFA
                vegas_acc = vegas_acc + ml_to_winpct(game_odds['ml_home'])

            day_results.append(result)
            result['line'] = int(result['line'])
            print('Bet:', result['bet_on'], result['line'], result['side_value'], result['k_risk'], result['net'])
        day_risk = 0
        day_net = 0
        for result in day_results:
            day_risk = day_risk + result['k_risk']
            day_net = day_net + result['net']
        risk_acc = risk_acc + day_risk
        acc = acc + day_net

        print('\n---------------------------------------------------------------')
        print(day,'-- total risk:',day_risk,'-- total net:',day_net,'-- acc:',acc)
        roi = 0 if risk_acc == 0 else acc/risk_acc*100
        print('ROI to date', roi)
        print('-----------------------------------------------------------------')
        day_summary = dict()
        day_summary['date'] = day
        day_summary['risk'] = day_risk
        day_summary['net'] = day_net
        day_summary['acc'] = acc
        all_results.extend(day_results)
        all_net.append(day_summary)
    print(my_acc, vegas_acc)

    total_risk = sum([g['k_risk'] for g in all_results])
    total_win = sum([g['net'] for g in all_results])

    print('ROI is', total_win/total_risk*100)

    import matplotlib.pyplot as plt

    plt.bar(range(len(all_net)), [day['acc'] for day in all_net])
    ticks = []
    for day in all_net:
        date = day['date']
        if int(date.split('-')[2]) in [10, 20, 1]:
            ticks.append(date[5:])
        else:
            ticks.append('')
    plt.xticks(range(len(all_net)), tuple(ticks), rotation = 'vertical')
    plt.show()

    with open(os.path.join('data','results','results_{}.json'.format(year)), 'r+') as f:
        f.truncate()
        json.dump(all_results, f)

    with open(os.path.join('data','results','profits_{}.json'.format(year)), 'r+') as f:
        f.truncate()
        json.dump(all_net, f)

    manifest = manifest.loc[:, ~manifest.columns.str.contains('^Unnamed')]
    manifest.to_csv(os.path.join('data','master.csv'), index=False)

if __name__ == '__main__':
    # if you `python3 main.py gr`, program will update relievers, otherwise as normal
    gr = False
    test = False
    if len(sys.argv) > 1:
        print(sys.argv[1])
        gr = sys.argv[1] == 'gr'
        test = sys.argv[1] == 'test'
    if test:
        test_year(year)
    else:
        # update_all(gr)
        main()