from scrapers.scraper_utils import get_days_in_season
import pandas as pd
import random
import json
import sys
import os

year = 2018

steamer_batters = pd.read_csv(os.path.join('data','steamer', 'steamer_hitters_{}_split.csv'.format(year)))
steamer_pitchers = pd.read_csv(os.path.join('data','steamer', 'steamer_pitchers_{}_split.csv'.format(year)))

hitter_logs = pd.read_csv(os.path.join('data','player_logs','batters_{}.csv'.format(year)))
pitcher_logs = pd.read_csv(os.path.join('data','player_logs','pitchers_{}.csv'.format(year)))

games = pd.read_csv(os.path.join('data','games','games_{}.csv'.format(year)))
park_factors = pd.read_csv(os.path.join('data','park_factors_general.csv'))

def batter_dict(batter_id, projections):
    batter_projections = projections.loc[projections['mlbamid'] == batter_id].to_dict('records')
    batter_projections = batter_projections[0]
    projections_accumulator = dict(
        k = batter_projections['K'] / batter_projections['PA'],
        bb = batter_projections['BB'] / batter_projections['PA'],
        hbp = batter_projections['HBP'] / batter_projections['PA'],
        hr = batter_projections['HR'] / batter_projections['PA'],
        triple = batter_projections['3B'] / batter_projections['PA'],
        double = batter_projections['2B'] / batter_projections['PA'],
        single = batter_projections['1B'] / batter_projections['PA'],
        mlb_id = batter_id,
        date = get_days_in_season(year)[0],
        bats = batter_projections['bats']
    )
    return projections_accumulator

def update_batter_projections(batter_id):
    batter_logs = hitter_logs.loc[hitter_logs['player_id'] == batter_id]
    print(batter_logs['player'].tolist()[0])
    batter_projections = steamer_batters.loc[(steamer_batters['pn'] == 1) & (steamer_batters['split'] == 'overall')]
    projections_accumulator = batter_dict(batter_id, batter_projections)
    baseline = dict(projections_accumulator)
    all_projections = []

    p_const = 400
    for ix, stat_line in batter_logs.iterrows():
        try:
            home_team = games.loc[games['key'] == stat_line['game_id']].iloc[0]['home']
        except:
            print('Game',stat_line['game_id'],'doesn\'t exist. Continuing')
            continue
        acc = dict(projections_accumulator)
        acc['date'] = stat_line['game_date']
        all_projections.append(acc)
        pf = park_factors[park_factors['Team'] == home_team].to_dict('records')[0]
        pa = stat_line['tpa']
        projections_accumulator['k'] = ((projections_accumulator['k'] * (p_const - pa)) + stat_line['so']) / p_const
        projections_accumulator['bb'] = ((projections_accumulator['bb'] * (p_const - pa)) + stat_line['bb']) / p_const
        projections_accumulator['hbp'] = ((projections_accumulator['hbp'] * (p_const - pa)) + stat_line['hbp']) / p_const
        projections_accumulator['hr'] = ((projections_accumulator['hr'] * (p_const - pa)) + stat_line['hr'] / (pf['HR'] / 100)) / p_const
        projections_accumulator['triple'] = ((projections_accumulator['triple'] * (p_const - pa)) + stat_line['t'] / (pf['3B'] / 100)) / p_const
        projections_accumulator['double'] = ((projections_accumulator['double'] * (p_const - pa)) + stat_line['d'] / (pf['2B'] / 100)) / p_const
        projections_accumulator['single'] = ((projections_accumulator['single'] * (p_const - pa)) + (stat_line['h'] - stat_line['hr'] - stat_line['t'] - stat_line['d']) / (pf['1B'] / 100)) / p_const

    vL_base = batter_dict(batter_id, steamer_batters[(steamer_batters['split'] == 'vL') & (steamer_batters['pn'] == 1)])
    vR_base = batter_dict(batter_id, steamer_batters[(steamer_batters['split'] == 'vR') & (steamer_batters['pn'] == 1)])
    acc = []
    keys = ['k','bb','hbp','hr','triple','double','single']
    for ros_proj in all_projections:
        transformations = { key: ros_proj[key]/baseline[key] for key in keys }
        vL = { 'vL_'+key: vL_base[key] * transformations[key] for key in keys }
        vR = { 'vR_'+key: vR_base[key] * transformations[key] for key in keys }
        combined = {**vL, **vR}
        combined['date'] = ros_proj['date']
        combined['mlb_id'] = ros_proj['mlb_id']
        combined['bats'] = ros_proj['bats']
        acc.append(combined)
    return pd.DataFrame(acc)

def pitcher_dict(projections):
    starter = projections[
        (projections['pn'] == 1) &
        (projections['role'] == 'SP')].to_dict('records')
    reliever = projections[
        (projections['pn'] == 1) &
        (projections['role'] == 'RP')].to_dict('records')

    keys = ['HBP/PA','SO/PA','BB/PA','1B/PA','2B/PA','3B/PA','HR/PA']
    if len(reliever) == 0:
        starter = starter[0]
        base = dict(throws = starter['Throws'], mlb_id = starter['mlbamid'], date = get_days_in_season(year)[0])
        for key in keys:
            base[key] = starter[key]
    elif len(starter) == 0:
        reliever = reliever[0]
        base = dict(throws = reliever['Throws'], mlb_id = reliever['mlbamid'], date = get_days_in_season(year)[0])
        for key in keys:
            base[key] = reliever[key]
    else:
        starter = starter[0]
        reliever = reliever[0]
        pct_starter = 0 if starter['TBF'] == 0 else (starter['TBF'] + reliever['TBF']) / starter['TBF']
        base = dict(throws = starter['Throws'], mlb_id = starter['mlbamid'], date = get_days_in_season(year)[0])
        for key in keys:
            base[key] = (starter[key] * pct_starter) + (reliever[key] * (1 - pct_starter))

    base["k"] = base.pop("SO/PA")
    base["bb"] = base.pop("BB/PA")
    base["hbp"] = base.pop("HBP/PA")
    base["single"] = base.pop("1B/PA")
    base["double"] = base.pop("2B/PA")
    base["triple"] = base.pop("3B/PA")
    base["hr"] = base.pop("HR/PA")
    return base


def update_pitcher_projections(pitcher_id):
    p_logs = pitcher_logs.loc[pitcher_logs['player_id'] == pitcher_id]
    print(p_logs['player_id'].tolist()[0])
    pitcher_projections = steamer_pitchers.loc[steamer_pitchers['mlbamid'] == pitcher_id]
    projections_accumulator = pitcher_dict(pitcher_projections)
    baseline = dict(projections_accumulator)
    all_projections = []
    #hackery as pitcher logs do not individually log non-hr hits
    all_hits = baseline['single'] + baseline['double'] + baseline['triple'] + baseline['hr']
    s_ratio = baseline['single'] / all_hits
    d_ratio = baseline['double'] / all_hits
    t_ratio = baseline['triple'] / all_hits

    p_const = 750
    for ix, stat_line in p_logs.iterrows():
        try:
            home_team = games.loc[games['key'] == stat_line['game_id']].iloc[0]['home']
        except:
            print('Game',stat_line['game_id'],'doesn\'t exist. Continuing')
            continue
        acc = dict(projections_accumulator)
        acc['date'] = stat_line['game_date']
        all_projections.append(acc)
        pf = park_factors[park_factors['Team'] == home_team].to_dict('records')[0]
        tbf = stat_line['tbf']
        projections_accumulator['k'] = ((projections_accumulator['k'] * (p_const - tbf)) + stat_line['so']) / p_const
        projections_accumulator['bb'] = ((projections_accumulator['bb'] * (p_const - tbf)) + stat_line['bb']) / p_const
        projections_accumulator['hbp'] = ((projections_accumulator['hbp'] * (p_const - tbf)) + stat_line['hb']) / p_const
        projections_accumulator['hr'] = ((projections_accumulator['hr'] * (p_const - tbf)) + stat_line['hr'] / (pf['HR'] / 100)) / p_const
        projections_accumulator['triple'] = ((projections_accumulator['triple'] * (p_const - tbf)) + ((stat_line['h'] - stat_line['hr']) * t_ratio) / (pf['3B'] / 100)) / p_const
        projections_accumulator['double'] = ((projections_accumulator['double'] * (p_const - tbf)) + ((stat_line['h'] - stat_line['hr']) * d_ratio) / (pf['2B'] / 100)) / p_const
        projections_accumulator['single'] = ((projections_accumulator['single'] * (p_const - tbf)) + ((stat_line['h'] - stat_line['hr']) * s_ratio) / (pf['1B'] / 100)) / p_const

    vL_projections = pitcher_projections[pitcher_projections['split'] == 'vL']
    vR_projections = pitcher_projections[pitcher_projections['split'] == 'vR']
    vL_base = pitcher_dict(vL_projections)
    vR_base = pitcher_dict(vR_projections)
    acc = []
    keys = ['k','bb','hbp','hr','triple','double','single']
    throws = vR_base['throws']
    mlb_id = vR_base['mlb_id']
    for ros_proj in all_projections:
        transformations = { key: ros_proj[key]/baseline[key] for key in keys }
        vL = { 'vL_'+key: vL_base[key] * transformations[key] for key in keys }
        vR = { 'vR_'+key: vR_base[key] * transformations[key] for key in keys }
        combined = {**vL, **vR}
        combined['date'] = ros_proj['date']
        combined['mlb_id'] = mlb_id
        combined['throws'] = throws
        acc.append(combined)
    return pd.DataFrame(acc)

if __name__ == '__main__':
    player_ids = list(set(pitcher_logs['player_id'].tolist()))
    steamer_ids = list(set(steamer_pitchers['mlbamid'].tolist()))
    all_pitchers = []
    for ix, player_id in enumerate(player_ids):
        if ix%25 ==0:
            print(ix,'/',len(player_ids))
        if player_id not in steamer_ids:
            print('No splits for pitcher', player_id, 'will continue')
            continue
        proj = update_pitcher_projections(player_id)
        all_pitchers.append(proj)
    df = pd.concat(all_pitchers).set_index(['mlb_id','date'])
    df.to_csv(os.path.join('data','projections','pitchers_{}.csv'.format(year)))

    player_ids = list(set(hitter_logs['player_id'].tolist()))
    steamer_ids = list(set(steamer_batters['mlbamid'].tolist()))
    all_hitters = []
    for player_id in player_ids:
        if player_id not in steamer_ids:
            print('No splits for batter', player_id, 'will continue')
            continue
        all_hitters.append(update_batter_projections(player_id))
    df = pd.concat(all_hitters).set_index(['mlb_id','date'])
    df.to_csv(os.path.join('data','projections','hitters_{}.csv'.format(year)))