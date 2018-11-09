import pandas as pd
import os
import copy
from math import floor

year = 2016

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
            print(retro_id)
            sys.exit()

def get_fangraphs_id_from_mlb(mlb_id):
    try:
        row = manifest[manifest['MLBID'] == mlb_id]
        return int(row['IDFANGRAPHS'].iloc[0])
    except:
        row = manifest2[manifest2['mlb_id'] == mlb_id]
        return int(row['fg_id'].iloc[0])

def accumulator_conditional(totals, current, numer, denom, thresh):
    if totals[denom] <= thresh:
        return (current * (thresh - totals[denom]) + totals[numer]) / thresh
    else:
        return totals[numer] / totals[denom]

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
        gb = gb + .44 * pa
        fb = fb + .35 * pa
        ld = ld + .21 * pa

    if not prev_2.empty:
        prev_2 = prev_2.iloc[0]
        gb = gb + float(prev_2['GB%'][:-1]) / 100.0 * 3 * int(prev_2['PA'])
        fb = fb + float(prev_2['FB%'][:-1]) / 100.0 * 3 * int(prev_2['PA'])
        ld = ld + float(prev_2['LD%'][:-1]) / 100.0 * 3 * int(prev_2['PA'])
        pa = pa + 3 * int(prev_2['PA'])
    else:
        gb = gb + .44 * 3 * 300
        fb = fb + .35 * 3 * 300
        ld = ld + .21 * 3 * 300
        pa = pa + 3 * 300

    if not prev_3.empty:
        prev_3 = prev_3.iloc[0]
        gb = gb + float(prev_3['GB%'][:-1]) / 100.0 * 1 * int(prev_3['PA'])
        fb = fb + float(prev_3['FB%'][:-1]) / 100.0 * 1 * int(prev_3['PA'])
        ld = ld + float(prev_3['LD%'][:-1]) / 100.0 * 1 * int(prev_3['PA'])
        pa = pa + 1 * int(prev_3['PA'])
    else:
        gb = gb + .44 * 1 * 300
        fb = fb + .35 * 1 * 300
        ld = ld + .21 * 1 * 300
        pa = pa + 1 * 300

    gb = gb / pa
    fb = fb / pa
    ld = ld / pa
    return gb, fb, ld

def generate_batter_stats(batters):
    dfs = []
    for batter in batters:
        mlb_id, name = get_mlb_id_from_retro(batter)
        logs = batter_logs[batter_logs['mlb_id'] == mlb_id]
        if logs.empty:
            continue
        projection = steamer_batters_split[
            (steamer_batters_split['mlbamid'] == mlb_id) &
            (steamer_batters_split['pn'] == 1) &
            (steamer_batters_split['split'] == 'overall')
        ]
        if projection.empty:
            print('No steamer for -', name, '- skipping')
            continue
        projection = projection.iloc[0]
        gb, fb, ld = get_bb_rates(mlb_id)
        proj_acc = dict(
            k_rate = projection['K'] / projection['PA'],
            bb_rate = projection['NIBB'] / projection['PA'],
            hbp_rate = projection['HBP'] / projection['PA'],
            hr_rate = projection['HR'] / projection['PA'],
            wraa_rate = projection['wRAA'] / projection['PA'],
            gb_rate = gb, #lgAvg
            fb_rate = fb, #lgAvg
            ld_rate = ld, #lgAvg
        )
        all_projections = []
        totals = dict(k=0, bb=0, hbp=0, hr=0, wraa=0, gb=0, fb=0, ld=0, pa=0, bip=0)
        for ix, stat_line in logs.iterrows():
            # link the dates of the projection to game dates and append to projections
            acc = copy.deepcopy(proj_acc)
            acc['date'] = stat_line['date']
            acc['mlb_id'] = mlb_id
            all_projections.append(acc)

            #then update the stats for the next game
            totals['k'] = totals['k'] + stat_line['k']
            totals['bb'] = totals['bb'] + stat_line['bb']
            totals['hbp'] = totals['hbp'] + stat_line['hbp']
            totals['wraa'] = totals['wraa'] + stat_line['wRAA']
            totals['hr'] = totals['hr'] + stat_line['hr']
            totals['gb'] = totals['gb'] + stat_line['gb']
            totals['fb'] = totals['fb'] + stat_line['fb']
            totals['ld'] = totals['ld'] + stat_line['ld']
            totals['pa'] = totals['pa'] + stat_line['pa']
            totals['bip'] = totals['bip'] + stat_line['gb'] + stat_line['fb'] + stat_line['ld']
            proj_acc['k_rate'] = accumulator_conditional(totals, proj_acc['k_rate'], 'k', 'pa', 60)
            proj_acc['bb_rate'] = accumulator_conditional(totals, proj_acc['bb_rate'], 'bb', 'pa', 120)
            proj_acc['hbp_rate'] = accumulator_conditional(totals, proj_acc['hbp_rate'], 'hbp', 'pa', 240)
            proj_acc['wraa_rate'] = accumulator_conditional(totals, proj_acc['wraa_rate'], 'wraa', 'pa', 400)
            proj_acc['hr_rate'] = accumulator_conditional(totals, proj_acc['hr_rate'], 'hbp', 'pa', 170)
            proj_acc['gb_rate'] = accumulator_conditional(totals, proj_acc['gb_rate'], 'gb', 'bip', 80)
            proj_acc['fb_rate'] = accumulator_conditional(totals, proj_acc['fb_rate'], 'fb', 'bip', 80)
            proj_acc['ld_rate'] = accumulator_conditional(totals, proj_acc['ld_rate'], 'ld', 'bip', 600)
        proj_acc['date'] = 'current'
        proj_acc['mlb_id'] = mlb_id
        all_projections.append(proj_acc)
        dfs.append(pd.DataFrame(all_projections))
    return pd.concat(dfs)

def generate_pitcher_stats(pitchers):
    dfs = []
    for pitcher in pitchers:
        mlb_id, name = get_mlb_id_from_retro(pitcher)
        logs = pitcher_logs[pitcher_logs['mlb_id'] == mlb_id]
        if logs.empty:
            continue
        projection = steamer_pitchers[steamer_pitchers['mlbamid'] == mlb_id]
        if projection.empty:
            print('No steamer for -', name, '- skipping')
            continue
        projection = projection.iloc[0]
        proj_acc = dict(
            k_rate = projection['Krate'],
            bb_rate = projection['BBrate'],
            hbp_rate = projection['HBPrate'],
            gb_rate = projection['GBrate'],
            fb_rate = projection['FBrate'],
            ld_rate = projection['LDrate'],
        )
        all_projections = []
        totals = dict(k=0,bb=0,hbp=0,gb=0,fb=0,ld=0,pa=0,bip=0)
        for ix, stat_line in logs.iterrows():
            # link the dates of the projection to game dates and append to projections
            acc = copy.deepcopy(proj_acc)
            acc['date'] = stat_line['date']
            acc['mlb_id'] = mlb_id
            all_projections.append(acc)

            #then update the stats for the next game
            totals['k'] = totals['k'] + stat_line['k']
            totals['bb'] = totals['bb'] + stat_line['bb']
            totals['hbp'] = totals['hbp'] + stat_line['hbp']
            totals['gb'] = totals['gb'] + stat_line['gb']
            totals['fb'] = totals['fb'] + stat_line['fb']
            totals['ld'] = totals['ld'] + stat_line['ld']
            totals['pa'] = totals['pa'] + stat_line['tbf']
            totals['bip'] = totals['bip'] + stat_line['gb'] + stat_line['fb'] + stat_line['ld']
            proj_acc['k_rate'] = accumulator_conditional(totals, proj_acc['k_rate'], 'k', 'pa', 75)
            proj_acc['bb_rate'] = accumulator_conditional(totals, proj_acc['bb_rate'], 'bb', 'pa', 170)
            proj_acc['hbp_rate'] = accumulator_conditional(totals, proj_acc['hbp_rate'], 'hbp', 'pa', 650)
            proj_acc['gb_rate'] = accumulator_conditional(totals, proj_acc['gb_rate'], 'gb', 'bip', 75)
            proj_acc['fb_rate'] = accumulator_conditional(totals, proj_acc['fb_rate'], 'fb', 'bip', 75)
            proj_acc['ld_rate'] = accumulator_conditional(totals, proj_acc['ld_rate'], 'ld', 'bip', 650)
        proj_acc['date'] = 'current'
        proj_acc['mlb_id'] = mlb_id
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
        batter_id, batter_name = get_mlb_id_from_retro(matchup['batter'])
        if batter_id not in batter_list:
            continue

        try:
            batter_proj = batter_stats[
                (batter_stats['mlb_id'] == batter_id) & (batter_stats['date'] == matchup['date'])
            ].iloc[0]
        except:
            print("Missing", batter_name, "on date", matchup['date'])
            continue

        try:
            pitcher_id, pitcher_name = get_mlb_id_from_retro(matchup['pitcher'])
            if pitcher_id not in pitcher_list:
                continue
            pitcher_proj = pitcher_stats[
                (pitcher_stats['mlb_id'] == pitcher_id) & (pitcher_stats['date'] == matchup['date'])
            ].iloc[0]
        except:
            print("Missing", pitcher_name, "on date", matchup['date'])
            continue

        if matchup['outcome'] != 'k' and matchup['outcome'] != 'bb' and matchup['outcome'] != 'hitbypitch':
            lines.append(dict(
                p_ld = pitcher_proj['ld_rate'],
                p_gb = pitcher_proj['gb_rate'],
                p_fb = pitcher_proj['fb_rate'],
                b_hr = batter_proj['hr_rate'],
                b_ld = batter_proj['ld_rate'],
                b_gb = batter_proj['gb_rate'],
                b_fb = batter_proj['fb_rate'],
                res_1b = int(matchup['outcome'] == 'single'),
                res_xbh = int(matchup['outcome'] == 'double') + int(matchup['outcome'] == 'triple'),
                res_hr = int(matchup['outcome'] == 'hr'),
                res_out = int(matchup['outcome'] == 'NonKOut'),
            ))
    df = pd.DataFrame(lines)
    return df

if __name__ == '__main__':
     # calc_siera(488984, '2017/10/07')
     all_batters = list(set(matchups['batter'].tolist()))
     batter_stats = generate_batter_stats(all_batters)
     all_pitchers = list(set([x for x in matchups['pitcher'].tolist() if not ',' in x]))
     pitcher_stats = generate_pitcher_stats(all_pitchers)
     matchup_results = get_matchup_results(batter_stats, pitcher_stats)
     matchup_results.to_csv(os.path.join('data','RFC_input','{}.csv'.format(year)))
