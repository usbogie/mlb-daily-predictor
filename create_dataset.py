import pandas as pd
import os
import copy
from datetime import datetime, timedelta
from math import floor
from scrapers.scraper_utils import fangraphs_to_mlb, team_leagues, get_days_in_season
from utils import get_baserunning_runs, get_batting_runs, get_fielding_runs, get_pitching_runs

year = 2015
pitcher_logs = pd.read_csv(os.path.join('data','player_logs','pitcher_logs_{}.csv'.format(year)))
batter_logs = pd.read_csv(os.path.join('data','player_logs','batter_logs_{}.csv'.format(year)))
steamer_pitchers = pd.read_csv(os.path.join('data','steamer', 'steamer_pitchers_{}.csv'.format(year)))
steamer_batters_split = pd.read_csv(os.path.join('data','steamer', 'steamer_hitters_{}_split.csv'.format(year)))
park_factors = pd.read_csv(os.path.join('data','park_factors_{}.csv'.format(year)))
manifest = pd.read_csv(os.path.join('data','master2.csv'), encoding='latin1')
manifest2 = pd.read_csv(os.path.join('data','master3.csv'), encoding='latin1')

league_stats = {
    'r_pa': {
        "2018_proj": .118,
        "2018": 0.117,
        "2017_proj": 0.114,
        "2017": 0.122,
        "2016_proj": 0.112,
        "2016": 0.118,
        "2015_proj": 0.110,
        "2015": 0.113,
        "2014": 0.108,
        "2013": 0.110,
        "2012": 0.114,
    },
    'wrc': {
        "AL": {
            # "2018_proj": .0118,
            "2018": 0.1196096776,
            # "2017_proj": 0.114,
            "2017": 0.12339457,
            # "2016_proj": 0.112,
            "2016": 0.1200802862,
            # "2015_proj": 0.110,
            "2015": 0.1157894737,
            "2014": 0.1099483851,
            "2013": 0.1136459562,
            "2012": 0.1169271653,
        },
        "NL": {
            # "2018_proj": .0118,
            "2018": 0.1221276113,
            # "2017_proj": 0.114,
            "2017": 0.1285654052,
            # "2016_proj": 0.112,
            "2016": 0.1231695337,
            # "2015_proj": 0.110,
            "2015": 0.1165836562,
            "2014": 0.1122841467,
            "2013": 0.1125012937,
            "2012": 0.1191642605,
        }
    },
}

def calc_wrcplus(al_nl, factor, games, pa, wraa):
    pf = factor/games
    wrcplus = (((wraa/pa + league_stats['r_pa'][str(year)]) + (league_stats['r_pa'][str(year)] - (pf/100 * league_stats['r_pa'][str(year)]))) / (league_stats['wrc'][al_nl][str(year)])) * 100
    return round(wrcplus, 2)

def generate_batter_stats(batters):
    dfs = []
    for mlb_id in batters:
        logs = batter_logs[batter_logs['mlb_id'] == mlb_id]
        if logs.empty:
            print("Empty logs for", mlb_id)
            continue
        logs = logs.sort_values(by='date')
        steamer = steamer_batters_split[
            (steamer_batters_split['mlbamid'] == mlb_id) &
            (steamer_batters_split['pn'] == 1) &
            (steamer_batters_split['split'] == 'overall')
        ]
        if steamer.empty:
            print("No steamer for", mlb_id)
            # continue
        else:
            steamer = steamer.iloc[0]

        if steamer.empty or isinstance(steamer['Team'], float):
            league_init = 'AL'
        else:
            league_init = team_leagues[steamer['Team'].lower().replace('laa','ana')] if steamer['Team'] != 'FA' else 'AL'
        proj = dict(
            pa = 0,
            wRAA = 0,
            wrcplus = 100 if steamer.empty else calc_wrcplus(league_init, 100, 1, steamer['PA'], steamer['wRAA']),
            mlb_id = mlb_id,
        )
        last_date = 0

        proj_acc = copy.deepcopy(proj)
        all_projections = []
        pfs_list = []
        teams_list = []
        games_played = 0
        pf = 100
        thresh = 200
        decay_coeff = 0.999
        for ix, stat_line in logs.iterrows():
            # print(proj_acc['wrcplus'])
            acc = copy.deepcopy(proj_acc)
            acc['date'] = stat_line['date']
            if steamer.empty:
                if acc['pa'] > 25:
                    all_projections.append(acc)
            else:
                all_projections.append(acc)

            if stat_line['pa'] == 0:
                # print('no plate appearances for', stat_line['name'], stat_line['date'])
                continue

            if last_date == 0:
                decay = 0
            else:
                decay = (datetime.strptime(stat_line['date'], '%Y-%m-%d') - datetime.strptime(last_date, '%Y-%m-%d')).days

            teams_list.append(team_leagues[stat_line['team']])
            league = 'AL' if teams_list.count('AL') > len(teams_list) * 0.5 else 'NL'
            pf = pf * (decay_coeff ** decay) + (park_factors[park_factors['Team'] == stat_line['team']].iloc[0]['Basic'] * 2 - 100)
            games_played = games_played * (decay_coeff ** decay) + 1
            proj_acc['pa'] = proj_acc['pa'] * (decay_coeff ** decay) + stat_line['pa']
            proj_acc['wRAA'] = proj_acc['wRAA'] * (decay_coeff ** decay) + stat_line['wRAA']
            if thresh > proj_acc['pa']:
                proj_acc['wrcplus'] = (calc_wrcplus(league, pf, games_played, proj_acc['pa'], proj_acc['wRAA']) * proj_acc['pa'] / thresh) + \
                                    (proj['wrcplus'] * (1 - proj_acc['pa'] / thresh))
            else:
                proj_acc['wrcplus'] = calc_wrcplus(league, pf, games_played, proj_acc['pa'], proj_acc['wRAA'])

            last_date = stat_line['date']
        # print(all_projections)
        try:
            proj_acc['date'] = (datetime.strptime(all_projections[-1]['date'], '%Y-%m-%d') + timedelta(1)).strftime('%Y-%m-%d')
        except:
            continue
        all_projections.append(proj_acc)
        dfs.append(pd.DataFrame(all_projections))
    df = pd.concat(dfs)
    df = df[['date', 'mlb_id', 'wRAA', 'wrcplus', 'pa']]
    print(df)
    return df

def calc_siera(gb, fb, k, bb, tbf, tbfSP):
    plus_minus = 2.232 * (((gb-fb) / tbf) ** 2)
    plus_minus = plus_minus * -1 if gb > fb else plus_minus
    siera = 5.952 - 15.219 * (k / tbf) \
            + 12.746 * ((k / tbf) ** 2) \
            - 0.385 * (bb / tbf) \
            + 10.671 * ((bb / tbf) ** 2) \
            - 2.844 * ((gb - fb) / tbf) \
            + 15.421 * (k / tbf) * (bb / tbf) \
            + 5.226 * (k / tbf) * ((gb - fb) / tbf) \
            + 10.150 * (bb / tbf) * ((gb - fb) / tbf) \
            + 0.246 * (tbfSP / tbf)
    return round(siera + plus_minus, 3)

def generate_pitcher_stats(pitchers):
    dfs = []
    for mlb_id in pitchers:
        logs = pitcher_logs[pitcher_logs['mlb_id'] == mlb_id]
        if logs.empty:
            print("Empty logs for", mlb_id)
            continue
        logs = logs.sort_values(by='date')
        steamer = steamer_pitchers[steamer_pitchers['mlbamid'] == mlb_id]
        if steamer.empty:
            print("No steamer for", mlb_id)
            # continue
        else:
            steamer = steamer.iloc[0]
        proj = dict(
            tbf = 0,
            tbfSP = 0,
            k = 0,
            bb = 0,
            gb = 0,
            fb = 0,
            ld = 0,
            siera = 4.11 if steamer.empty else calc_siera(steamer['GB'], steamer['FB'], steamer['K'], steamer['BB'], steamer['TBF'], steamer['TBF'] * steamer['GS'] / steamer['G']),
            mlb_id = mlb_id,
        )
        last_date = 0

        proj_acc = copy.deepcopy(proj)
        all_projections = []
        thresh = 75
        decay_coeff = 0.999
        for ix, stat_line in logs.iterrows():
            if stat_line['tbf'] == 0:
                print('no batters faced for', stat_line['name'], stat_line['date'])
                continue

            if last_date == 0:
                decay = 0
            else:
                decay = (datetime.strptime(stat_line['date'], '%Y-%m-%d') - datetime.strptime(last_date, '%Y-%m-%d')).days

            acc = copy.deepcopy(proj_acc)
            acc['date'] = stat_line['date']
            if steamer.empty:
                if acc['tbf'] > 0:
                    all_projections.append(acc)
            else:
                all_projections.append(acc)

            proj_acc['tbfSP'] = proj_acc['tbfSP'] * (decay_coeff**decay) + (stat_line['tbf'] if stat_line['gs'] == 1 else 0)
            proj_acc['tbf'] = proj_acc['tbf']  * (decay_coeff**decay) + stat_line['tbf']
            proj_acc['k'] = proj_acc['k'] * (decay_coeff**decay) + stat_line['k']
            proj_acc['bb'] = proj_acc['bb'] * (decay_coeff**decay) + stat_line['bb']
            proj_acc['gb'] = proj_acc['gb'] * (decay_coeff**decay) + stat_line['gb']
            proj_acc['fb'] = proj_acc['fb'] * (decay_coeff**decay) + stat_line['fb']
            proj_acc['ld'] = proj_acc['ld'] * (decay_coeff**decay) + stat_line['ld']
            if thresh > proj_acc['tbf']:
                proj_acc['siera'] = (calc_siera(proj_acc['gb'],  proj_acc['fb'], proj_acc['k'], proj_acc['bb'], proj_acc['tbf'], proj_acc['tbfSP']) \
                                     * proj_acc['tbf'] / thresh) + (proj['siera'] * (1 - proj_acc['tbf'] / thresh))
            else:
                proj_acc['siera'] = calc_siera(proj_acc['gb'],  proj_acc['fb'], proj_acc['k'], proj_acc['bb'], proj_acc['tbf'], proj_acc['tbfSP'])

            last_date = stat_line['date']

        try:
            proj_acc['date'] = (datetime.strptime(all_projections[-1]['date'], '%Y-%m-%d') + timedelta(1)).strftime('%Y-%m-%d')
        except:
            continue
        all_projections.append(proj_acc)
        dfs.append(pd.DataFrame(all_projections))

    df = pd.concat(dfs)
    df = df[['date', 'mlb_id', 'siera', 'tbf', 'tbfSP', 'k', 'bb', 'ld', 'gb', 'fb']]
    print(df)
    return df

def create_team_stats():
    days = get_days_in_season(year)
    games = pd.read_csv(os.path.join('data','games','games_{}.csv'.format(year)))
    lineups = pd.read_csv(os.path.join('data','lineups','lineups_{}.csv'.format(year)))
    manifest = pd.read_csv(os.path.join('data','master.csv'))
    batter_projections = pd.read_csv(os.path.join('data','projections','batter_proj_{}.csv'.format(year)))
    pitcher_projections = pd.read_csv(os.path.join('data','projections','pitcher_proj_{}.csv'.format(year)))
    steamer_batters = pd.read_csv(os.path.join('data','steamer', 'steamer_hitters_{}_split.csv'.format(year)))
    steamer_batters['fullname'] = steamer_batters[['firstname', 'lastname']].apply(lambda x: ' '.join(x), axis=1)
    # steamer_pitchers = pd.read_csv(os.path.join('data','steamer','steamer_pitchers_{}_split.csv'.format(year)))
    # steamer_pitchers['fullname'] = steamer_pitchers[['firstname', 'lastname']].apply(lambda x: ' '.join(x), axis=1)

    inputs = []
    for day in days:
        slate = games[games['date'] == day]
        day_results = []
        for index, game in slate.iterrows():
            try:
                away_lineup = lineups[(lineups['key'] == game['key']) & (game['away'] == lineups['name'])].to_dict('records')[0]
                home_lineup = lineups[(lineups['key'] == game['key']) & (game['home'] == lineups['name'])].to_dict('records')[0]
            except:
                print('mismatch of game/lineup keys for', game['key'], 'continuing')
                continue

            # print(day,game['away'],'vs',game['home'])

            away_batting_runs = get_batting_runs.calculate(away_lineup, game['date'], manifest, batter_projections)
            home_batting_runs = get_batting_runs.calculate(home_lineup, game['date'], manifest, batter_projections)
            away_pitching_runs = get_pitching_runs.calculate(away_lineup, game['date'], manifest, pitcher_projections)
            # print('vs', end=" ")
            home_pitching_runs = get_pitching_runs.calculate(home_lineup, game['date'], manifest, pitcher_projections)
            # print()
            # print(game['away_score'], '-', game['home_score'])
            if not away_batting_runs or not home_batting_runs or not away_pitching_runs or not home_pitching_runs:
                print("Could not find ^, continue")
                continue

            # dh = team_leagues[team_codes[game['home']]] == 'AL'
            # away_player_ids = [manifest[manifest['fantasy_labs'] == away_lineup[str(x)+'_id']].iloc[0]['mlb_id']
            #                    for x in range(1,10)]
            # home_player_ids = [manifest[manifest['fantasy_labs'] == home_lineup[str(x)+'_id']].iloc[0]['mlb_id']
            #                    for x in range(1,10)]
            # away_pitcher_id = manifest[manifest['fantasy_labs'] == away_lineup['10_id']].iloc[0]['mlb_id']
            # home_pitcher_id = manifest[manifest['fantasy_labs'] == home_lineup['10_id']].iloc[0]['mlb_id']
            # away_fielding_runs = get_fielding_runs.calculate(dh, away_pitcher_id, away_player_ids, steamer_batters)
            # home_fielding_runs = get_fielding_runs.calculate(dh, home_pitcher_id, home_player_ids, steamer_batters)

            # away_baserunning_runs = get_baserunning_runs.calculate(away_lineup, steamer_batters, manifest)
            # home_baserunning_runs = get_baserunning_runs.calculate(home_lineup, steamer_batters, manifest)

            input_away = dict(
                key = game['key'],
                batters_home = 0,
                b1 = away_batting_runs[0],
                b2 = away_batting_runs[1],
                b3 = away_batting_runs[2],
                b4 = away_batting_runs[3],
                b5 = away_batting_runs[4],
                b6 = away_batting_runs[5],
                b7 = away_batting_runs[6],
                b8 = away_batting_runs[7],
                b9 = away_batting_runs[8],
                pitching = home_pitching_runs,
                runs_scored = game['away_score'],
            )

            input_home = dict(
                key = game['key'],
                batters_home = 1,
                b1 = home_batting_runs[0],
                b2 = home_batting_runs[1],
                b3 = home_batting_runs[2],
                b4 = home_batting_runs[3],
                b5 = home_batting_runs[4],
                b6 = home_batting_runs[5],
                b7 = home_batting_runs[6],
                b8 = home_batting_runs[7],
                b9 = home_batting_runs[8],
                pitching = away_pitching_runs,
                runs_scored = game['home_score'],
            )
            inputs.extend([input_away, input_home])
    inputs_df = pd.DataFrame(inputs)
    print(inputs_df)
    inputs_df.to_csv(os.path.join('data','tensor_inputs','{}.csv'.format(year)), index=False)
    manifest = manifest.loc[:, ~manifest.columns.str.contains('^Unnamed')]
    manifest.to_csv(os.path.join('data','master.csv'), index=False)

if __name__ == '__main__':
    import random
    all_batters = list(set(batter_logs['mlb_id'].tolist()))
    random.shuffle(all_batters)
    # all_batters = [664023]
    batter_stats = generate_batter_stats(all_batters)
    batter_stats.to_csv(os.path.join('data',
                                     'projections',
                                     'batter_proj_{}.csv'.format(year)),
                        index=False)
    all_pitchers = list(set(pitcher_logs['mlb_id'].tolist()))
    # all_pitchers = [595014]
    pitcher_stats = generate_pitcher_stats(all_pitchers)
    pitcher_stats.to_csv(os.path.join('data','projections',
                                      'pitcher_proj_{}.csv'.format(year)),
                         index=False)
    create_team_stats()
