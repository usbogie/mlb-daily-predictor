import pandas as pd
import os
import copy
from datetime import datetime, timedelta
from math import floor
from scrapers.scraper_utils import fangraphs_to_mlb, team_leagues

year = 2018

pitcher_logs = pd.read_csv(os.path.join('data','player_logs','pitcher_logs_{}.csv'.format(year)))
batter_logs = pd.read_csv(os.path.join('data','player_logs','batter_logs_{}.csv'.format(year)))
steamer_pitchers = pd.read_csv(os.path.join('data','steamer', 'steamer_pitchers_{}.csv'.format(year)))
steamer_batters_split = pd.read_csv(os.path.join('data','steamer', 'steamer_hitters_{}_split.csv'.format(year)))
park_factors = pd.read_csv(os.path.join('data','park_factors_general.csv'))
manifest = pd.read_csv(os.path.join('data','master2.csv'), encoding='latin1')
manifest2 = pd.read_csv(os.path.join('data','master3.csv'), encoding='latin1')

def get_fangraphs_id_from_mlb(mlb_id):
    try:
        row = manifest[manifest['MLBID'] == mlb_id]
        return int(row['IDFANGRAPHS'].iloc[0])
    except:
        row = manifest2[manifest2['mlb_id'] == mlb_id]
        return int(row['fg_id'].iloc[0])

league_stats = {
    'r_pa': {
        "2018_proj": .0118,
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
        "AL": {
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

def calc_wRAApf(team_list, pa, wraa):

    return (wraa/pa + league_stats['r_pa'][year]) + (league_stats['r_pa'][year] - (Park_Factor * league_stats['r_pa'][year])) / (League_wRC_excluding pitchers/PA) x 100

def generate_batter_stats(batters):
    dfs = []
    for mlb_id in batters:
        logs = batter_logs[batter_logs['mlb_id'] == mlb_id]
        if logs.empty:
            print("Empty logs for", mlb_id)
            continue
        steamer = steamer_batters_split[
            (steamer_batters_split['mlbamid'] == mlb_id) &
            (steamer_batters_split['pn'] == 1) &
            (steamer_batters_split['split'] == 'overall')
        ]
        if steamer.empty:
            print("No steamer for", mlb_id)
            continue
        steamer = steamer.iloc[0]
        proj = dict(
            pa = 0,
            wRAA = 0,
            throws = steamer['bats'],
            wRAApf = calc_wRAApf(steamer['PA'], steamer['wRAA']),
            mlb_id = mlb_id,
        )
        last_date = 0

        proj_acc = copy.deepcopy(proj)
        all_projections = []
        thresh = 325
        for ix, stat_line in logs.iterrows():
            if stat_line['pa'] == 0:
                print('no plate appearances for', stat_line['name'], stat_line['date'])
            acc = copy.deepcopy(proj_acc)
            acc['date'] = stat_line['date']
            all_projections.append(acc)
            proj_acc['pa'] = proj_acc['pa'] + stat_line['pa']
            proj_acc['wRAA'] = proj_acc['wRAA'] + stat_line['wRAA']
            if thresh > proj_acc['tbf']:
                proj_acc['wRAApf'] = (calc_wRAApf(proj_acc) * proj_acc['tbf'] / thresh) + \
                                    (proj['siera'] * (1 - proj_acc['tbf'] / thresh))
            else:
                proj_acc['siera'] = calc_siera(proj_acc)

            last_date = stat_line['date']

        proj_acc['date'] = (datetime.strptime(all_projections[-1]['date'], '%Y-%m-%d') + timedelta(1)).strftime('%Y-%m-%d')
        all_projections.append(proj_acc)
        dfs.append(pd.DataFrame(all_projections))

    df = pd.concat(dfs)
    df = df[['date', 'mlb_id', 'siera', 'tbf', 'tbfSP', 'k', 'bb', 'ld', 'gb', 'fb']]
    return df

def calc_siera(proj_acc):
    plus_minus = 4.920 * (((proj_acc['gb']-proj_acc['fb']) / proj_acc['tbf']) ** 2)
    plus_minus = plus_minus * -1 if proj_acc['gb'] > proj_acc['fb'] else plus_minus
    siera = 5.534 - 15.518 * (proj_acc['k'] / proj_acc['tbf']) \
            + 9.146 * ((proj_acc['k'] / proj_acc['tbf']) ** 2) \
            + 8.648 * (proj_acc['bb'] / proj_acc['tbf']) \
            + 27.252 * ((proj_acc['bb'] / proj_acc['tbf']) ** 2) \
            - 2.298 * ((proj_acc['gb'] - proj_acc['fb']) / proj_acc['tbf']) \
            - 4.036 * (proj_acc['k']/proj_acc['tbf'])*(proj_acc['bb']/proj_acc['tbf']) \
            + 5.155 * (proj_acc['k']/proj_acc['tbf'])*((proj_acc['gb'] - proj_acc['fb'])/proj_acc['tbf']) \
            - 4.546 * (proj_acc['bb']/proj_acc['tbf'])*((proj_acc['gb'] - proj_acc['fb'])/proj_acc['tbf']) \
            + 0.367 * (proj_acc['tbfSP'] / proj_acc['tbf'])
    return round(siera + plus_minus, 3)

def generate_pitcher_stats(pitchers):
    dfs = []
    for mlb_id in pitchers:
        logs = pitcher_logs[pitcher_logs['mlb_id'] == mlb_id]
        if logs.empty:
            print("Empty logs for", mlb_id)
            continue
        steamer = steamer_pitchers[steamer_pitchers['mlbamid'] == mlb_id]
        if steamer.empty:
            print("No steamer for", mlb_id)
            continue
        steamer = steamer.iloc[0]
        proj = dict(
            tbf = 0,
            tbfSP = 0,
            k = 0,
            bb = 0,
            gb = 0,
            fb = 0,
            ld = 0,
            siera = steamer['SIERA'],
            throws = steamer['Throws'],
            mlb_id = mlb_id,
        )
        last_date = 0

        proj_acc = copy.deepcopy(proj)
        all_projections = []
        thresh = 150
        for ix, stat_line in logs.iterrows():
            if stat_line['tbf'] == 0:
                print('no batters faced for', stat_line['name'], stat_line['date'])
            acc = copy.deepcopy(proj_acc)
            acc['date'] = stat_line['date']
            all_projections.append(acc)
            proj_acc['tbf'] = proj_acc['tbf'] + stat_line['tbf']
            proj_acc['tbfSP'] = proj_acc['tbfSP'] + (stat_line['tbf'] if stat_line['gs'] == 1 else 0)
            proj_acc['k'] = proj_acc['k'] + stat_line['k']
            proj_acc['bb'] = proj_acc['bb'] + stat_line['bb']
            proj_acc['gb'] = proj_acc['gb'] + stat_line['gb']
            proj_acc['fb'] = proj_acc['fb'] + stat_line['fb']
            proj_acc['ld'] = proj_acc['ld'] + stat_line['ld']
            if thresh > proj_acc['tbf']:
                proj_acc['siera'] = (calc_siera(proj_acc) * proj_acc['tbf'] / thresh) + \
                                    (proj['siera'] * (1 - proj_acc['tbf'] / thresh))
            else:
                proj_acc['siera'] = calc_siera(proj_acc)

            last_date = stat_line['date']

        proj_acc['date'] = (datetime.strptime(all_projections[-1]['date'], '%Y-%m-%d') + timedelta(1)).strftime('%Y-%m-%d')
        all_projections.append(proj_acc)
        dfs.append(pd.DataFrame(all_projections))

    df = pd.concat(dfs)
    df = df[['date', 'mlb_id', 'siera', 'tbf', 'tbfSP', 'k', 'bb', 'ld', 'gb', 'fb']]
    return df

if __name__ == '__main__':
     # all_batters = list(set(batter_logs['mlb_id'].tolist()))
     # batter_stats = generate_batter_stats(all_batters)
     # batter_stats.to_csv(os.path.join('data',
     #                                  'projections',
     #                                  'batter_proj_{}.csv'.format(year)),
     #                     index=False)
     all_pitchers = list(set(pitcher_logs['mlb_id'].tolist()))
     pitcher_stats = generate_pitcher_stats(all_pitchers)
     pitcher_stats.to_csv(os.path.join('data','projections',
                                       'pitcher_proj_{}.csv'.format(year)),
                          index=False)
     # matchup_results = get_matchup_results(batter_stats, pitcher_stats)
     # matchup_results.to_csv(os.path.join('data',
     #                                     'RFC_input',
     #                                     '{}.csv'.format(year)),
     #                        index=False)
