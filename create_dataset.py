import pandas as pd
import os
import copy
from datetime import datetime, timedelta
from math import floor

year = 2015

bb_path = os.path.join('data','batted_ball_profiles')
prev_1_df = pd.read_csv(os.path.join(bb_path,'{}.csv'.format(year-1)))
prev_2_df = pd.read_csv(os.path.join(bb_path,'{}.csv'.format(year-2)))
prev_3_df = pd.read_csv(os.path.join(bb_path,'{}.csv'.format(year-3)))
pitcher_logs = pd.read_csv(os.path.join('data','player_logs','pitcher_logs_{}.csv'.format(year)))
batter_logs = pd.read_csv(os.path.join('data','player_logs','batter_logs_{}.csv'.format(year)))
steamer_pitchers = pd.read_csv(os.path.join('data','steamer', 'steamer_pitchers_{}.csv'.format(year)))
steamer_batters_split = pd.read_csv(os.path.join('data','steamer', 'steamer_hitters_{}_split.csv'.format(year)))
matchups = pd.read_csv(os.path.join('data','retrosheet', str(year), '{}_matchups.csv'.format(year)))
manifest = pd.read_csv(os.path.join('data','master2.csv'), encoding='latin1')
manifest2 = pd.read_csv(os.path.join('data','master3.csv'), encoding='latin1')

def get_mlb_id_from_retro(retro_id):
    try:
        row = manifest[manifest['RETROID'] == retro_id]
        return int(row['MLBID'].iloc[0]), row['MLBNAME'].iloc[0]
    except:
        try:
            row = manifest2[manifest2['retro_id'] == retro_id]
            return int(row['mlb_id'].iloc[0]), row['mlb_name'].iloc[0]
        except:
            print(retro_id, "not found in manifest")
            sys.exit()

def get_fangraphs_id_from_mlb(mlb_id):
    try:
        row = manifest[manifest['MLBID'] == mlb_id]
        return int(row['IDFANGRAPHS'].iloc[0])
    except:
        row = manifest2[manifest2['mlb_id'] == mlb_id]
        return int(row['fg_id'].iloc[0])

def accumulator_conditional(stat_line, proj_rate, numer, denom, thresh, numer_acc, denom_acc, decay):
    denom_num = (stat_line['fb'] + stat_line['gb'] + stat_line['ld']) if denom == 'bip' else stat_line[denom]
    denom_acc = denom_acc * (.998 ** decay) + denom_num
    numer_acc = numer_acc * (.998 ** decay) + stat_line[numer]

    # print(stat_line['date'], stat_line[numer], numer, denom, numer_acc, denom_acc)
    if denom_acc < (1.6 * thresh):
        return ((proj_rate * ((1.6 * thresh) - denom_acc) + numer_acc) / (1.6 * thresh)), numer_acc, denom_acc

    return (numer_acc / denom_acc), numer_acc, denom_acc

def get_bb_rates(mlb_id):
    fg_id = get_fangraphs_id_from_mlb(mlb_id)
    prev_1 = prev_1_df[prev_1_df['playerid'] == fg_id]
    prev_2 = prev_2_df[prev_2_df['playerid'] == fg_id]
    prev_3 = prev_3_df[prev_3_df['playerid'] == fg_id]

    gb = fb = ld = 0
    pa = 0
    if not prev_1.empty:
        prev_1 = prev_1.iloc[0]
        pa = pa + 6 * int(prev_1['PA'])
        gb = gb + (float(prev_1['GB%'][:-1]) / 100.0 * pa)
        fb = fb + (float(prev_1['FB%'][:-1]) / 100.0 * pa)
        ld = ld + (float(prev_1['LD%'][:-1]) / 100.0 * pa)
    else:
        pa = pa + 6 * 300
        gb = gb + .432 * pa
        fb = fb + .354 * pa
        ld = ld + .214 * pa

    if not prev_2.empty:
        prev_2 = prev_2.iloc[0]
        gb = gb + float(prev_2['GB%'][:-1]) / 100.0 * 3 * int(prev_2['PA'])
        fb = fb + float(prev_2['FB%'][:-1]) / 100.0 * 3 * int(prev_2['PA'])
        ld = ld + float(prev_2['LD%'][:-1]) / 100.0 * 3 * int(prev_2['PA'])
        pa = pa + 3 * int(prev_2['PA'])
    else:
        gb = gb + .432 * 3 * 300
        fb = fb + .354 * 3 * 300
        ld = ld + .214 * 3 * 300
        pa = pa + 3 * 300

    if not prev_3.empty:
        prev_3 = prev_3.iloc[0]
        gb = gb + float(prev_3['GB%'][:-1]) / 100.0 * 1 * int(prev_3['PA'])
        fb = fb + float(prev_3['FB%'][:-1]) / 100.0 * 1 * int(prev_3['PA'])
        ld = ld + float(prev_3['LD%'][:-1]) / 100.0 * 1 * int(prev_3['PA'])
        pa = pa + 1 * int(prev_3['PA'])
    else:
        gb = gb + .442 * 1 * 300
        fb = fb + .354 * 1 * 300
        ld = ld + .214 * 1 * 300
        pa = pa + 1 * 300

    gb = gb / pa
    fb = fb / pa
    ld = ld / pa
    return gb, fb, ld

def generate_batter_stats(batters):
    dfs = []
    for mlb_id in batters:
        logs = batter_logs[batter_logs['mlb_id'] == mlb_id]
        if logs.empty:
            continue
        projection = steamer_batters_split[
            (steamer_batters_split['mlbamid'] == mlb_id) &
            (steamer_batters_split['pn'] == 1) &
            (steamer_batters_split['split'] == 'overall')
        ]
        if projection.empty:
            print('No steamer for -', mlb_id, '- skipping')
            continue
        projection = projection.iloc[0]
        gb, fb, ld = get_bb_rates(mlb_id)
        proj = dict(
            k_rate = projection['K'] / projection['PA'],
            bb_rate = projection['NIBB'] / projection['PA'],
            hbp_rate = projection['HBP'] / projection['PA'],
            hr_rate = projection['HR'] / projection['PA'],
            hr_fb_rate = (projection['HR'] / (projection['AB'] - projection['K'])) / fb,
            gb_rate = gb,
            fb_rate = fb,
            ld_rate = ld,
            bats = projection['bats'],
            mlb_id = int(mlb_id)
        )
        proj_acc = copy.deepcopy(proj)
        all_projections = []
        last_date = 0
        k_numer=k_denom=bb_numer=bb_denom=hbp_numer=hbp_denom=hr_numer=hr_denom=0
        hrfb_numer=hrfb_denom=gb_numer=gb_denom=fb_numer=fb_denom=ld_numer=ld_denom=0
        for ix, stat_line in logs.iterrows():
            # link the dates of the projection to game dates and append to projections
            acc = copy.deepcopy(proj_acc)
            acc['date'] = stat_line['date']
            all_projections.append(acc)

            if last_date == 0:
                decay = 0
            else:
                decay = (datetime.strptime(stat_line['date'], '%Y-%m-%d') - datetime.strptime(last_date, '%Y-%m-%d')).days

            proj_acc['k_rate'], k_numer, k_denom = accumulator_conditional(stat_line, proj['k_rate'], 'k', 'pa', 110, k_numer, k_denom, decay)
            proj_acc['bb_rate'], bb_numer, bb_denom = accumulator_conditional(stat_line, proj['bb_rate'], 'bb', 'pa', 180, bb_numer, bb_denom, decay)
            proj_acc['hbp_rate'], hbp_numer, hbp_denom = accumulator_conditional(stat_line, proj['hbp_rate'], 'hbp', 'pa', 500, hbp_numer, hbp_denom, decay)
            proj_acc['hr_rate'], hr_numer, hr_denom = accumulator_conditional(stat_line, proj['hr_rate'], 'hr', 'pa', 340, hr_numer, hr_denom, decay)
            proj_acc['hr_fb_rate'], hrfb_numer, hrfb_denom = accumulator_conditional(stat_line, proj['hr_fb_rate'], 'hr', 'fb', 60, hrfb_numer, hrfb_denom, decay)
            proj_acc['gb_rate'], gb_numer, gb_denom = accumulator_conditional(stat_line, proj['gb_rate'], 'gb', 'bip', 115, gb_numer, gb_denom, decay)
            proj_acc['fb_rate'], fb_numer, fb_denom = accumulator_conditional(stat_line, proj['fb_rate'], 'fb', 'bip', 185, fb_numer, fb_denom, decay)
            proj_acc['ld_rate'], ld_numer, ld_denom = accumulator_conditional(stat_line, proj['ld_rate'], 'ld', 'bip', 795, ld_numer, ld_denom, decay)

            last_date = stat_line['date']

        proj_acc['date'] = (datetime.strptime(all_projections[-1]['date'], '%Y-%m-%d') + timedelta(1)).strftime('%Y-%m-%d')
        all_projections.append(proj_acc)
        dfs.append(pd.DataFrame(all_projections))
    return pd.concat(dfs)

def generate_pitcher_stats(pitchers):
    dfs = []
    for mlb_id in pitchers:
        logs = pitcher_logs[pitcher_logs['mlb_id'] == mlb_id]
        if logs.empty:
            continue
        projection = steamer_pitchers[steamer_pitchers['mlbamid'] == mlb_id]
        if projection.empty:
            print('No steamer for -', mlb_id, '- skipping')
            continue
        projection = projection.iloc[0]
        proj = dict(
            k_rate = projection['Krate'],
            bb_rate = projection['BBrate'],
            hbp_rate = projection['HBPrate'],
            hr_rate = projection['HR'] / projection['TBF'],
            hr_fb_rate = projection['HR/FB'],
            gb_rate = projection['GBrate'],
            fb_rate = projection['FBrate'],
            ld_rate = projection['LDrate'],
            throws = projection['Throws'],
            mlb_id = mlb_id,
        )
        proj_acc = copy.deepcopy(proj)
        all_projections = []
        last_date = 0
        k_numer=k_denom=bb_numer=bb_denom=hbp_numer=hbp_denom=hr_numer=hr_denom=0
        hrfb_numer=hrfb_denom=gb_numer=gb_denom=fb_numer=fb_denom=ld_numer=ld_denom=0
        for ix, stat_line in logs.iterrows():
            # link the dates of the projection to game dates and append to projections
            acc = copy.deepcopy(proj_acc)
            acc['date'] = stat_line['date']
            all_projections.append(acc)

            if last_date == 0:
                decay = 0
            else:
                decay = (datetime.strptime(stat_line['date'], '%Y-%m-%d') - datetime.strptime(last_date, '%Y-%m-%d')).days

            proj_acc['k_rate'], k_numer, k_denom = accumulator_conditional(stat_line, proj['k_rate'], 'k', 'tbf', 130, k_numer, k_denom, decay)
            proj_acc['bb_rate'], bb_numer, bb_denom = accumulator_conditional(stat_line, proj['bb_rate'], 'bb', 'tbf', 305, bb_numer, bb_denom, decay)
            proj_acc['hbp_rate'], hbp_numer, hbp_denom = accumulator_conditional(stat_line, proj['hbp_rate'], 'hbp', 'tbf', 1350, hbp_numer, hbp_denom, decay)
            proj_acc['hr_rate'], hr_numer, hr_denom = accumulator_conditional(stat_line, proj['hr_rate'], 'hr', 'tbf', 1300, hr_numer, hr_denom, decay)
            proj_acc['hr_fb_rate'], hrfb_numer, hrfb_denom = accumulator_conditional(stat_line, proj['hr_fb_rate'], 'hr', 'fb', 1240, hrfb_numer, hrfb_denom, decay)
            proj_acc['gb_rate'], gb_numer, gb_denom = accumulator_conditional(stat_line, proj['gb_rate'], 'gb', 'bip', 105, gb_numer, gb_denom, decay)
            proj_acc['fb_rate'], fb_numer, fb_denom = accumulator_conditional(stat_line, proj['fb_rate'], 'fb', 'bip', 205, fb_numer, fb_denom, decay)
            proj_acc['ld_rate'], ld_numer, ld_denom = accumulator_conditional(stat_line, proj['ld_rate'], 'ld', 'bip', 2000, ld_numer, ld_denom, decay)

            last_date = stat_line['date']

        proj_acc['date'] = (datetime.strptime(all_projections[-1]['date'], '%Y-%m-%d') + timedelta(1)).strftime('%Y-%m-%d')
        all_projections.append(proj_acc)
        dfs.append(pd.DataFrame(all_projections))
    return pd.concat(dfs)

def get_matchup_results(batter_stats, pitcher_stats):
    batter_list = list(set(batter_stats['mlb_id'].tolist()))
    pitcher_list = list(set(pitcher_stats['mlb_id'].tolist()))
    lines = []
    home_team = None
    for ix, matchup in matchups.iterrows():
        if home_team != matchup['key'].split('mlb-')[1]:
            print(matchup['key'].split('mlb-')[1])
            home_team = matchup['key'].split('mlb-')[1]

        try:
            batter_id, batter_name = get_mlb_id_from_retro(matchup['batter'])
            if batter_id not in batter_list:
                continue
            batter_proj = batter_stats[
                (batter_stats['mlb_id'] == batter_id) & (batter_stats['date'] == matchup['date'])
            ].iloc[0]
        except:
            print("Missing batter", batter_name, "on date", matchup['date'])
            print(batter_stats[(batter_stats['mlb_id'] == batter_id)])
            continue

        try:
            pitcher_id, pitcher_name = get_mlb_id_from_retro(matchup['pitcher'])
            if pitcher_id not in pitcher_list:
                continue
            pitcher_proj = pitcher_stats[
                (pitcher_stats['mlb_id'] == pitcher_id) & (pitcher_stats['date'] == matchup['date'])
            ].iloc[0]
        except:
            print("Missing pitcher", pitcher_name, "on date", matchup['date'])
            continue

        if pitcher_proj['throws'] == 'B':
            pitcher_proj['throws'] == 'R'
        if batter_proj['bats'] == 'B' or batter_proj['bats'] == 'S':
            batter_proj['bats'] = 'L' if pitcher_proj['throws'] == 'R' else 'R'

        lines.append(dict(
            matchup = "{}_v_{}".format(pitcher_proj['throws'], batter_proj['bats']),
            p_hr = pitcher_proj['hr_rate'],
            p_ld = pitcher_proj['ld_rate'],
            p_gb = pitcher_proj['gb_rate'],
            p_fb = pitcher_proj['fb_rate'],
            p_so = pitcher_proj['k_rate'],
            p_bb = pitcher_proj['bb_rate'],
            p_hbp = pitcher_proj['hbp_rate'],
            b_hr = batter_proj['hr_rate'],
            b_ld = batter_proj['ld_rate'],
            b_gb = batter_proj['gb_rate'],
            b_fb = batter_proj['fb_rate'],
            b_so = batter_proj['k_rate'],
            b_bb = batter_proj['bb_rate'],
            b_hbp = batter_proj['hbp_rate'],
            res_so = int(matchup['outcome'] == 'k'),
            res_nonso = int(matchup['outcome'] != 'k'),
            res_bbhbp = int(matchup['outcome'] == 'bb' or
                            matchup['outcome'] == 'hitbypitch'),
            res_nonbbhbp = int(matchup['outcome'] != 'bb' and
                               matchup['outcome'] != 'hitbypitch' and
                               matchup['outcome'] != 'k'),
            res_hr = int(matchup['outcome'] == 'homerun'),
            res_nonhr = int(matchup['outcome'] != 'bb' and
                            matchup['outcome'] != 'hitbypitch' and
                            matchup['outcome'] != 'k' and
                            matchup['outcome'] != 'hr'),
            res_hit = int(matchup['outcome'] == 'single' or
                          matchup['outcome'] == 'double' or
                          matchup['outcome'] == 'triple'),
            res_out = int(matchup['outcome'] == 'NonKOut'),
        ))
    df = pd.DataFrame(lines)
    return df

if __name__ == '__main__':
     all_batters = list(set(batter_logs['mlb_id'].tolist()))
     batter_stats = generate_batter_stats(all_batters)
     batter_stats.to_csv(os.path.join('data',
                                      'projections',
                                      'batter_proj_{}.csv'.format(year)),
                         index=False)
     all_pitchers = list(set(pitcher_logs['mlb_id'].tolist()))
     pitcher_stats = generate_pitcher_stats(all_pitchers)
     pitcher_stats.to_csv(os.path.join('data',
                                       'projections',
                                       'pitcher_proj_{}.csv'.format(year)),
                          index=False)
     matchup_results = get_matchup_results(batter_stats, pitcher_stats)
     matchup_results.to_csv(os.path.join('data',
                                         'RFC_input',
                                         '{}.csv'.format(year)),
                            index=False)
