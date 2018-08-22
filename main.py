from datetime import datetime
from scrapers.scraper_utils import team_codes, get_days_in_season
from storage.Game import Game
from simulation.MonteCarlo import MonteCarlo
from utils.converters import winpct_to_ml, over_total_pct, d_to_a, ml_to_winpct, third_kelly_calculator, amount_won
from lineups.lineups import get_batting_stats, get_pitching_stats, get_team_defense
from lineups.matchups import generate_matchups, calc_averages
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

starters_to_ignore = {2017: ['Cesar Valdez', 'Jeremy Guthrie', 'Christian Bergman',
    'Hector Velazquez','Sam Gaviglio','Eric Skoglund','Austin Bibens-Dirkx','Tyler Pill','Mike Bolsinger',
    'Dinelson Lamet','Mike Pelfrey','Randall Delgado','Vance Worley','David Holmberg','Dayan Diaz',
    'Paolo Espino','Sean Newcomb','Nik Turley','Marco Gonzales','Daniel Gossett','Francis Martes',
    'Adam Wilk','Andrew Moore','Luis Castillo','Mark Leiter','Felix Jorge','Luke Farrell',
    'Chris O\'Grady','Caleb Smith','Kyle Lloyd','Erick Fedde','Troy Scribner','Nick Tepesch',
    'Chris Rowley','Chad Bettis','Andrew Albers','Aaron Slegers','T.J. McFarland','Tim Melville',
    'Tyler Mahle','Dillon Peters','Jack Flaherty','Onelki Garcia','Chad Bell','Artie Lewicki',
    'Luiz Gohara','Gabriel Ynoa','Myles Jaye','Jen-Ho Tseng','Aaron Wilkerson','Deck McGuire',
    'Chris Volstad','Jacob Turner','Ryan Weber','Lisalverto Bonilla','Jacob Turner'],
                      2018: ['Jonny Venters']}

def main():
    bankroll = 1000
    manifest = pd.read_csv(os.path.join('data','master.csv'))
    with open(os.path.join('data','relievers.json')) as f:
        all_relievers = json.load(f)
    batter_projections = pd.read_csv(os.path.join('data','projections','hitters_{}.csv'.format(year)))
    pitcher_projections = pd.read_csv(os.path.join('data','projections','pitchers_{}.csv'.format(year)))
    steamer_batters_general = pd.read_csv(os.path.join('data','steamer', 'steamer_hitters_{}.csv'.format(year)))
    steamer_batters = pd.read_csv(os.path.join('data','steamer', 'steamer_hitters_{}_split.csv'.format(year)))
    steamer_batters['fullname'] = steamer_batters[['firstname', 'lastname']].apply(lambda x: ' '.join(x), axis=1)
    steamer_pitchers = pd.read_csv(os.path.join('data','steamer','steamer_pitchers_{}_split.csv'.format(year)))
    steamer_pitchers['fullname'] = steamer_pitchers[['firstname', 'lastname']].apply(lambda x: ' '.join(x), axis=1)
    steamer_starters = pd.read_csv(os.path.join('data','steamer','steamer_pitchers_{}.csv'.format(year)))
    today = datetime.now().strftime('%Y-%m-%d')
    games = pd.read_csv(os.path.join('data','lines','today.csv'))
    lineups = pd.read_csv(os.path.join('data','lineups','today.csv'))
    park_factors = pd.read_csv(os.path.join('data','park_factors_handedness.csv'))
    game_outputs = []
    league_avgs = calc_averages(steamer_batters)
    for index, game in games.iterrows():
        print('\n')
        game_obj = Game(game['date'],game['time'],game['away'],game['home'])
        print('Simulating game:',today,game['time'],game['away'],game['home'])
        try:
            away_lineup = lineups[(lineups['key'] == game['key']) & (game['away'] == lineups['name'])].to_dict('records')[0]
            home_lineup = lineups[(lineups['key'] == game['key']) & (game['home'] == lineups['name'])].to_dict('records')[0]
        except:
            print("bad lineups, continue")
            continue

        away_output = dict(team=game['away'], lineup=away_lineup['lineup_status'])
        home_output = dict(team=game['home'], lineup=home_lineup['lineup_status'])
        away_lineup_stats = get_batting_stats(manifest, batter_projections, steamer_batters, away_lineup, game['date'])
        home_lineup_stats = get_batting_stats(manifest, batter_projections, steamer_batters, home_lineup, game['date'])
        away_pitching = get_pitching_stats(manifest, pitcher_projections, all_relievers, steamer_pitchers, steamer_starters, away_lineup, game['date'], test=False)
        home_pitching = get_pitching_stats(manifest, pitcher_projections, all_relievers, steamer_pitchers, steamer_starters, home_lineup, game['date'], test=False)
        if not away_pitching or not home_pitching or not away_lineup_stats or not home_lineup_stats:
            print('SOMETHING WRONG MAYBE CHECK IT OUT')
            continue

        away_defense = get_team_defense(away_lineup_stats, steamer_batters_general)
        home_defense = get_team_defense(home_lineup_stats, steamer_batters_general)
        pf = park_factors[park_factors['Team']==game['home']].to_dict(orient='records')

        all_matchups = generate_matchups(pf,steamer_batters, home_pitching, away_pitching, home_lineup_stats, away_lineup_stats, home_defense, away_defense, league_avgs)
        print('Away lineup is', away_lineup['lineup_status'],'|| Home lineup is', home_lineup['lineup_status'])
        mcGame = MonteCarlo(game_obj,away_lineup_stats,home_lineup_stats,away_pitching,home_pitching, all_matchups)
        mcGame.sim_games()

        print('Vegas away ML:',d_to_a(game['ml_away']),'|| Vegas home ML:',d_to_a(game['ml_home']))
        away_output['ml'] = d_to_a(game['ml_away'])
        home_output['ml'] = d_to_a(game['ml_home'])

        results = mcGame.sim_results()

        value = lambda pct, odds: round(100 * pct - ml_to_winpct(odds),1)

        away_output['ml_proj'] = winpct_to_ml(1 - results['home_win_prob'])
        home_output['ml_proj'] = winpct_to_ml(results['home_win_prob'])
        away_output['ml_value'] = value(1 - results['home_win_prob'], game['ml_away'])
        home_output['ml_value'] = value(results['home_win_prob'], game['ml_home'])
        kelly_away = third_kelly_calculator(game['ml_away'], 1 - results['home_win_prob'])
        kelly_home = third_kelly_calculator(game['ml_home'], results['home_win_prob'])
        away_output['kelly_risk'] = '${}'.format(round(bankroll*kelly_away/100,0))
        home_output['kelly_risk'] = '${}'.format(round(bankroll*kelly_home/100,0))
        print('Away implied money line:', away_output['ml_proj'], 'Value:', away_output['ml_value'], '%')
        print('Home implied money line:', home_output['ml_proj'], 'Value:', home_output['ml_value'], '%')
        print('Kelly br%: away {} ${}'.format(round(kelly_away,1),int(bankroll*kelly_away/100)))
        print('Kelly br%: home {} ${}'.format(round(kelly_home,1),int(bankroll*kelly_home/100)))

        if 'rl_away' in game and game['rl_away'] == game['rl_away']:
            print('Vegas away RL:',d_to_a(game['rl_away']),'|| Vegas home RL:',d_to_a(game['rl_home']))
            away_output['rl'] = d_to_a(game['rl_away'])
            home_output['rl'] = d_to_a(game['rl_home'])

            if game['ml_away'] <= 2 and game['ml_home'] <= 2:
                rl_fav = 'away' if game['rl_home'] < 2 else 'home'
            else:
                rl_fav = 'away' if game['ml_away'] < game['ml_home'] else 'home'

            if rl_fav == 'away':
                away_rl_win_pct = 1 - results['home_dog_rl_prob']
                home_rl_win_pct = results['home_dog_rl_prob']
            else:
                away_rl_win_pct = 1 - results['home_fav_rl_prob']
                home_rl_win_pct = results['home_fav_rl_prob']

            away_output['rl_proj'] = winpct_to_ml(away_rl_win_pct)
            home_output['rl_proj'] = winpct_to_ml(home_rl_win_pct)
            away_output['rl_value'] = value(away_rl_win_pct, game['rl_away'])
            home_output['rl_value'] = value(home_rl_win_pct, game['rl_home'])
            print('Implied away run line:', away_output['rl_proj'], 'Value:', away_output['rl_value'], '%')
            print('Implied home run line:', home_output['rl_proj'], 'Value:', home_output['rl_value'], '%')
        else:
            away_output['rl'] = home_output['rl'] = 'NA'
            away_output['rl_proj'] = home_output['rl_proj'] = 'NA'
            away_output['rl_value'] = home_output['rl_value'] = 'NA'

        if 'total_line' in game and game['total_line'] == game['total_line']:
            print('Vegas over:',game['total_line'],d_to_a(game['over_odds']))
            away_output['total'] = str(game['total_line'])+' '+str(d_to_a(game['over_odds']))
            home_output['total'] = str(game['total_line'])+' '+str(d_to_a(game['under_odds']))

            over_prob = over_total_pct(mcGame.comb_histo, game['total_line'])

            away_output['total_value'] = value(over_prob, game['over_odds'])
            home_output['total_value'] = value((1 - over_prob), game['under_odds'])
            print('Implied over line:', winpct_to_ml(over_prob), 'Value:', away_output['total_value'], '%')
            print('Implied under line:', winpct_to_ml(1-over_prob), 'Value:', home_output['total_value'], '%')
        else:
            away_output['total'] = home_output['total'] = 'NA'
            away_output['total_value'] = home_output['total_value'] = 'NA'

        if 'ml_away_f5' in game and 'ml_away_f5' in game and game['ml_away_f5'] == game['ml_away_f5']:
            print('Vegas away F5 ML:',d_to_a(game['ml_away_f5']),'|| Vegas home F5 ML:',d_to_a(game['ml_home_f5']))
            away_output['ml_f5'] = d_to_a(game['ml_away_f5'])
            home_output['ml_f5'] = d_to_a(game['ml_home_f5'])

            away_output['ml_proj_f5'] = winpct_to_ml(1 - results['f5_home_win_prob'])
            home_output['ml_proj_f5'] = winpct_to_ml(results['f5_home_win_prob'])
            away_output['ml_value_f5'] = value(1 - results['f5_home_win_prob'], game['ml_away_f5'])
            home_output['ml_value_f5'] = value(results['f5_home_win_prob'], game['ml_home_f5'])
            print('Implied away F5 money line:', away_output['ml_proj_f5'], 'Value:', away_output['ml_value_f5'], '%')
            print('Implied home F5 money line:', home_output['ml_proj_f5'], 'Value:', home_output['ml_value_f5'], '%')
        else:
            away_output['ml_f5'] = home_output['ml_f5'] = 'NA'
            away_output['ml_proj_f5'] = home_output['ml_proj_f5'] = 'NA'
            away_output['ml_value_f5'] = home_output['ml_value_f5'] = 'NA'

        if 'rl_away_f5' in game and game['rl_away_f5'] == game['rl_away_f5']:
            print('Vegas away F5 RL:',d_to_a(game['rl_away_f5']),'|| Vegas home F5 RL:',d_to_a(game['rl_home_f5']))
            away_output['rl_f5'] = d_to_a(game['rl_away_f5'])
            home_output['rl_f5'] = d_to_a(game['rl_home_f5'])

            if game['ml_away_f5'] <= 2 and game['ml_home_f5'] <= 2:
                rl_fav = 'away' if game['rl_home_f5'] < 2 else 'home'
            else:
                rl_fav = 'away' if game['ml_away_f5'] < game['ml_home_f5'] else 'home'

            if rl_fav == 'away':
                f5_away_rl_win_pct = 1 - results['f5_home_dog_win_prob']
                f5_home_rl_win_pct = results['f5_home_dog_win_prob']
            else:
                f5_away_rl_win_pct = 1 - results['f5_home_fav_win_prob']
                f5_home_rl_win_pct = results['f5_home_fav_win_prob']

            away_output['rl_proj_f5'] = winpct_to_ml(f5_away_rl_win_pct)
            home_output['rl_proj_f5'] = winpct_to_ml(f5_home_rl_win_pct)
            away_output['rl_value_f5'] = value(f5_away_rl_win_pct, game['rl_away_f5'])
            home_output['rl_value_f5'] = value(f5_home_rl_win_pct, game['rl_home_f5'])
            print('Away F5 implied run line:', away_output['rl_proj_f5'], 'Value:', away_output['rl_value_f5'], '%')
            print('Home F5 implied run line:', home_output['rl_proj_f5'], 'Value:', home_output['rl_value_f5'], '%')
        else:
            away_output['rl_f5'] = home_output['rl_f5'] = 'NA'
            away_output['rl_proj_f5'] = home_output['rl_proj_f5'] = 'NA'
            away_output['rl_value_f5'] = home_output['rl_value_f5'] = 'NA'

        if 'total_line_f5' in game and game['total_line_f5'] == game['total_line_f5'] and game['total_line_f5'] < 100:
            print('Vegas F5 over total:',game['total_line_f5'], d_to_a(game['over_odds_f5']))
            away_output['total_f5'] = str(game['total_line_f5'])+' '+str(d_to_a(game['over_odds_f5']))
            home_output['total_f5'] = str(game['total_line_f5'])+' '+str(d_to_a(game['under_odds_f5']))

            f5_over_prob = over_total_pct(mcGame.f5_comb_histo,game['total_line_f5'])

            away_output['total_value_f5'] = value(f5_over_prob, game['over_odds_f5'])
            home_output['total_value_f5'] = value((1 - f5_over_prob), game['under_odds_f5'])
            print('F5 over implied line:', winpct_to_ml(f5_over_prob), 'Value:', away_output['total_value_f5'], '%')
            print('F5 under implied line:', winpct_to_ml(1-f5_over_prob), 'Value:',home_output['total_value_f5'], '%')
        else:
            away_output['total_f5'] = home_output['total_f5'] = 'NA'
            away_output['total_value_f5'] = home_output['total_value_f5'] = 'NA'

        away_output['sc_in_first'] = round(results['score_in_first'] * 100, 2)
        home_output['sc_in_first'] = winpct_to_ml(results['score_in_first'])

        print('Score in first pct:', away_output['sc_in_first'],'Implied line:', home_output['sc_in_first'])

        game_outputs.append((game['time'], away_output, home_output))
    gsheets_upload.update_spreadsheet(game_outputs)

    manifest = manifest.loc[:, ~manifest.columns.str.contains('^Unnamed')]
    manifest.to_csv(os.path.join('data','master.csv'), index=False)

def test_year(year):
    all_relievers = []
    bankroll = 1000
    days = get_days_in_season(year)
    games = pd.read_csv(os.path.join('data','games','games_{}.csv'.format(year)))
    lines = pd.read_csv(os.path.join('data','lines','lines_{}.csv'.format(year)))
    lineups = pd.read_csv(os.path.join('data','lineups','lineups_{}.csv'.format(year)))
    park_factors = pd.read_csv(os.path.join('data','park_factors_handedness.csv'))
    manifest = pd.read_csv(os.path.join('data','master.csv'))
    batter_projections = pd.read_csv(os.path.join('data','projections','hitters_{}.csv'.format(year)))
    pitcher_projections = pd.read_csv(os.path.join('data','projections','pitchers_{}.csv'.format(year)))
    steamer_batters_general = pd.read_csv(os.path.join('data','steamer', 'steamer_hitters_{}.csv'.format(year)))
    steamer_batters = pd.read_csv(os.path.join('data','steamer', 'steamer_hitters_{}_split.csv'.format(year)))
    steamer_batters['fullname'] = steamer_batters[['firstname', 'lastname']].apply(lambda x: ' '.join(x), axis=1)
    steamer_pitchers = pd.read_csv(os.path.join('data','steamer','steamer_pitchers_{}_split.csv'.format(year)))
    steamer_pitchers['fullname'] = steamer_pitchers[['firstname', 'lastname']].apply(lambda x: ' '.join(x), axis=1)
    steamer_starters = pd.read_csv(os.path.join('data','steamer','steamer_pitchers_{}.csv'.format(year)))
    bullpens = pd.read_csv(os.path.join('data','lineups','bullpens_{}.csv'.format(year)))
    league_avgs = calc_averages(steamer_batters)

    all_results = []
    all_net = []
    t_all_results = []
    t_all_net = []
    acc = 0
    risk_acc = 0
    t_acc = 0
    t_risk_acc = 0
    my_acc = 0
    vegas_acc = 0
    for day in days:
        slate = games[games['date'] == day]
        day_results = []
        for index, game in slate.iterrows():
            game_obj = Game(game['date'],'12:05p',game['away'],game['home'])
            try:
                away_lineup = lineups[(lineups['key'] == game['key']) & (game['away'] == lineups['name'])].to_dict('records')[0]
                home_lineup = lineups[(lineups['key'] == game['key']) & (game['home'] == lineups['name'])].to_dict('records')[0]
            except:
                print('mismatch of game/lineup keys for', game['key'], 'continuing')
                continue

            if away_lineup['10_name'] in starters_to_ignore[year] or home_lineup['10_name'] in starters_to_ignore[year]:
                print('Starter {} has no projections. Continue'.format(away_lineup['10_name']))
                print('Starter {} has no projections. Continue\n'.format(home_lineup['10_name']))
                continue

            try:
                game_odds = lines[lines['key'] == game['key']].to_dict('records')[0]
            except:
                print('something wrong with game odds')
                continue

            away_lineup_stats = get_batting_stats(manifest, batter_projections, steamer_batters, away_lineup, game['date'])
            home_lineup_stats = get_batting_stats(manifest, batter_projections, steamer_batters, home_lineup, game['date'])
            away_pitching = get_pitching_stats(manifest, pitcher_projections, all_relievers, steamer_pitchers, steamer_starters, away_lineup, game['date'], test=True, bullpens=bullpens)
            home_pitching = get_pitching_stats(manifest, pitcher_projections, all_relievers, steamer_pitchers, steamer_starters, home_lineup, game['date'], test=True, bullpens=bullpens)
            if not away_pitching or not home_pitching or not away_lineup_stats or not home_lineup_stats:
                print('SOMETHING WRONG MAYBE CHECK IT OUT')
                continue
            pf = park_factors[park_factors['Team']==game['home']].to_dict(orient='records')
            away_defense = get_team_defense(away_lineup_stats, steamer_batters_general)
            home_defense = get_team_defense(home_lineup_stats, steamer_batters_general)

            print('Simulating game:',day,game['away'],'vs',game['home'])
            all_matchups = generate_matchups(pf,steamer_batters, home_pitching, away_pitching, home_lineup_stats, away_lineup_stats, home_defense, away_defense, league_avgs)
            mcGame = MonteCarlo(game_obj,away_lineup_stats,home_lineup_stats,away_pitching,home_pitching,all_matchups)
            try:
                mcGame.sim_games(test=True)
            except:
                print('Issue, attempting SIM again')
                mcGame.sim_games(test=True)

            mcGameResults = mcGame.sim_results()
            value = lambda pct, odds: round(100 * pct - ml_to_winpct(odds),1)

            try:
                over_pct = over_total_pct(mcGame.comb_histo, game_odds['total_line'])
            except:
                print('odds messed up, continue')
                continue

            result = dict(
                away = game['away'],
                home = game['home'],
                away_ml = d_to_a(game_odds['ml_away']),
                home_ml = d_to_a(game_odds['ml_home']),
                away_ml_proj = winpct_to_ml(1 - mcGameResults['home_win_prob']),
                home_ml_proj = winpct_to_ml(mcGameResults['home_win_prob']),
                over_odds = d_to_a(game_odds['over_odds']),
                under_odds = d_to_a(game_odds['under_odds']),
                over_proj = winpct_to_ml(over_pct),
                under_proj = winpct_to_ml(1 - over_pct),
                total = game_odds['total_line'],
            )

            value_away = value(1 - mcGameResults['home_win_prob'], game_odds['ml_away'])
            value_home = value(mcGameResults['home_win_prob'], game_odds['ml_home'])

            kelly_away = third_kelly_calculator(game_odds['ml_away'], 1 - mcGameResults['home_win_prob']) if value_away >= 0 else 0
            kelly_home = third_kelly_calculator(game_odds['ml_home'], mcGameResults['home_win_prob']) if value_home >= 0 else 0

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
                my_acc = my_acc + 1 - mcGameResults['home_win_prob']
                vegas_acc = vegas_acc + ml_to_winpct(game_odds['ml_away'])
            elif game['home_score'] > game['away_score']:
                if result['bet_on'] == result['home']:
                    result['net'] = amount_won(result['k_risk'], game_odds['ml_home'])
                    result['line'] = d_to_a(game_odds['ml_home'])
                elif result['bet_on'] == result['away']:
                    result['net'] = result['k_risk'] * -1
                    result['line'] = d_to_a(game_odds['ml_away'])
                my_acc = my_acc + mcGameResults['home_win_prob']
                vegas_acc = vegas_acc + ml_to_winpct(game_odds['ml_home'])

            over_value = value(over_pct, game_odds['over_odds'])
            under_value = value(1 - over_pct, game_odds['under_odds'])

            if over_value > 0 and game['home'] != 'Colorado Rockies':
                result['t_risk'] = int(third_kelly_calculator(game_odds['over_odds'], over_pct) * 5)
                if game['away_score'] + game['home_score'] > game_odds['total_line']:
                    result['t_net'] = int(amount_won(result['t_risk'], game_odds['over_odds']))
                elif game['away_score'] + game['home_score'] < game_odds['total_line']:
                    result['t_net'] = -1 * result['t_risk']
                else:
                    result['t_net'] = 0
                result['t_bet_on'] = 'Over'
                result['t_value'] = over_value
            elif under_value > 0 and game['home'] != 'Colorado Rockies':
                result['t_risk'] = int(third_kelly_calculator(game_odds['under_odds'], 1-over_pct) * 5)
                if game['away_score'] + game['home_score'] < game_odds['total_line']:
                    result['t_net'] = int(amount_won(result['t_risk'], game_odds['under_odds']))
                elif game['away_score'] + game['home_score'] > game_odds['total_line']:
                    result['t_net'] = -1 * result['t_risk']
                else:
                    result['t_net'] = 0
                result['t_bet_on'] = 'Under'
                result['t_value'] = under_value
            else:
                result['t_risk'] = 0
                result['t_net'] = 0
                result['t_value'] = 0
                result['t_bet_on'] = 'no bet'
            day_results.append(result)
            result['line'] = int(result['line'])
            print('Money Line:', result['bet_on'], result['line'], result['k_risk'], result['net'])
            print('Total:', result['t_bet_on'], result['total'], 'Final:', game['away_score'] + game['home_score'], result['t_risk'], result['t_net'])
        day_risk = 0
        day_net = 0
        t_day_risk = 0
        t_day_net = 0
        for result in day_results:
            day_risk = day_risk + result['k_risk']
            day_net = day_net + result['net']
            t_day_risk = t_day_risk + result['t_risk']
            t_day_net = t_day_net + result['t_net']
        risk_acc = risk_acc + day_risk
        t_risk_acc = t_risk_acc + t_day_risk
        acc = acc + day_net
        t_acc = t_acc + t_day_net
        print(day,'-- total risk:',day_risk,'-- total net:',day_net,'-- acc:',acc)
        roi = 0 if risk_acc == 0 else acc/risk_acc*100
        print('ROI to date', roi)
        print(day,'-- total t_risk:',t_day_risk,'-- total t_net:',t_day_net,'-- t_acc:',t_acc)
        roi = 0 if t_risk_acc == 0 else t_acc/t_risk_acc*100
        print('ROI to date', roi)
        day_summary = dict()
        day_summary['date'] = day
        day_summary['risk'] = day_risk
        day_summary['net'] = day_net
        day_summary['acc'] = acc
        day_summary['t_risk'] = t_day_risk
        day_summary['t_net'] = t_day_net
        day_summary['t_acc'] = t_acc
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
        print('testing')
        test_year(year)
    else:
        update_all(gr)
        main()
