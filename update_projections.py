from scrapers.scraper_utils import get_days_in_season, team_codes
import pandas as pd
import random
import json
import sys
import os
import copy
from datetime import datetime, timedelta

year = 2018

def accumulator_conditional(totals, current, numer, denom, thresh):
    if totals[denom] <= thresh:
        return (current * (thresh - totals[denom]) + totals[numer]) / thresh
    else:
        return totals[numer] / totals[denom]

def batter_dict(batter_id, projections):
    batter_projections = projections[(projections['mlbamid'] == batter_id) & (projections['pn'] == 1)].to_dict('records')
    batter_projections = batter_projections[0]
    proj_acc = dict(
        k = batter_projections['K'] / batter_projections['PA'],
        bb = batter_projections['BB'] / batter_projections['PA'],
        hbp = batter_projections['HBP'] / batter_projections['PA'],
        hr = batter_projections['HR'] / batter_projections['PA'],
        triple = batter_projections['3B'] / batter_projections['PA'],
        double = batter_projections['2B'] / batter_projections['PA'],
        single = batter_projections['1B'] / batter_projections['PA'],
        date = get_days_in_season(year)[0],
        bats = batter_projections['bats']
    )
    return proj_acc

def update_batter_projections(batter_id, hitter_logs, steamer_batters):
    with open(os.path.join('data','temps.json')) as f:
        temps = json.load(f)
    park_factors = pd.read_csv(os.path.join('data','park_factors_general.csv'))
    games = pd.read_csv(os.path.join('data','games','games_{}.csv'.format(year)))
    batter_logs = hitter_logs[hitter_logs['player_id'] == batter_id]
    print(batter_logs['player'].tolist()[0])
    batter_projections = steamer_batters[steamer_batters['split'] == 'overall']
    proj_acc = batter_dict(batter_id, batter_projections)
    baseline = copy.deepcopy(proj_acc)
    all_projections = []

    p_const = 300
    totals = dict(pa=0, k=0, bb=0, hbp=0, hr=0, single=0, double=0, triple=0)
    for ix, stat_line in batter_logs.iterrows():
        try:
            home_team = games[games['key'] == stat_line['game_id']].iloc[0]['home']
        except:
            print('Game',stat_line['game_id'],'doesn\'t exist. Continuing')
            continue

        acc = copy.deepcopy(proj_acc)
        acc['date'] = stat_line['game_date']
        try:
            temp_hit_adj = 0.8416988 + (1.025144 - 0.8416988)/(1 + (temps[acc['date']][home_team]/92.86499) ** 4.391434)
            temp_hr_adj = 0.3639859 + (1.571536 - 0.3639859)/(1 + (temps[acc['date']][home_team]/67.64016) ** 1.381388)
        except:
            print(games[games['key'] == stat_line['game_id']].iloc[0])
            temp_hit_adj = 1
            temp_hr_adj = 1
        all_projections.append(acc)
        pf = park_factors[park_factors['Team'] == home_team].to_dict('records')[0]
        totals['pa'] = totals['pa'] + stat_line['tpa']
        totals['k'] = totals['k'] + stat_line['so']
        totals['bb'] = totals['bb'] + stat_line['bb']
        totals['hbp'] = totals['hbp'] + stat_line['hbp']
        totals['hr'] = totals['hr'] + stat_line['hr']
        totals['triple'] = totals['triple'] + stat_line['t']
        totals['double'] = totals['double'] + stat_line['d']
        totals['single'] = totals['single'] + stat_line['h'] - stat_line['hr'] - stat_line['t'] - stat_line['d']
        proj_acc['k'] = accumulator_conditional(totals, proj_acc['k'], 'k', 'pa', 60)
        proj_acc['bb'] = accumulator_conditional(totals, proj_acc['bb'], 'bb', 'pa', 120)
        proj_acc['hbp'] = accumulator_conditional(totals, proj_acc['hbp'], 'hbp', 'pa', 240)
        proj_acc['hr'] = accumulator_conditional(totals, proj_acc['hr'], 'hr', 'pa', 170)
        proj_acc['triple'] = accumulator_conditional(totals, proj_acc['triple'], 'triple', 'pa', 1610)
        proj_acc['double'] = accumulator_conditional(totals, proj_acc['double'], 'double', 'pa', 1610)
        proj_acc['single'] = accumulator_conditional(totals, proj_acc['single'], 'single', 'pa', 290)
    proj_acc['date'] = (datetime.strptime(all_projections[-1]['date'], '%Y-%m-%d') + timedelta(1)).strftime('%Y-%m-%d')
    all_projections.append(proj_acc)
    vL_base = batter_dict(batter_id, steamer_batters[steamer_batters['split'] == 'vL'])
    vR_base = batter_dict(batter_id, steamer_batters[steamer_batters['split'] == 'vR'])
    acc = []
    keys = ['k','bb','hbp','hr','triple','double','single']
    for ros_proj in all_projections:
        transformations = { key: ros_proj[key]/baseline[key] for key in keys }
        vL = { 'vL_'+key: vL_base[key] * transformations[key] for key in keys }
        vR = { 'vR_'+key: vR_base[key] * transformations[key] for key in keys }
        combined = {**vL, **vR}
        combined['date'] = ros_proj['date']
        combined['mlb_id'] = batter_id
        combined['bats'] = ros_proj['bats']
        acc.append(combined)
    return pd.DataFrame(acc)

def pitcher_dict(pitcher_id, projections):
    starter = projections[
        (projections['mlbamid'] == pitcher_id) &
        (projections['pn'] == 1) &
        (projections['role'] == 'SP')].to_dict('records')
    reliever = projections[
        (projections['mlbamid'] == pitcher_id) &
        (projections['pn'] == 1) &
        (projections['role'] == 'RP')].to_dict('records')

    keys = ['HBP/PA','SO/PA','BB/PA','1B/PA','2B/PA','3B/PA','HR/PA']
    if len(reliever) == 0:
        starter = starter[0]
        base = dict(throws = starter['Throws'], date = get_days_in_season(year)[0])
        for key in keys:
            base[key] = starter[key]
    elif len(starter) == 0:
        reliever = reliever[0]
        base = dict(throws = reliever['Throws'], date = get_days_in_season(year)[0])
        for key in keys:
            base[key] = reliever[key]
    else:
        starter = starter[0]
        reliever = reliever[0]
        pct_starter = 0 if starter['TBF'] == 0 else (starter['TBF'] + reliever['TBF']) / starter['TBF']
        base = dict(throws = starter['Throws'], date = get_days_in_season(year)[0])
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


def update_pitcher_projections(pitcher_id, pitcher_logs, steamer_pitchers):
    with open(os.path.join('data','temps.json')) as f:
        temps = json.load(f)
    park_factors = pd.read_csv(os.path.join('data','park_factors_general.csv'))
    games = pd.read_csv(os.path.join('data','games','games_{}.csv'.format(year)))
    p_logs = pitcher_logs[pitcher_logs['player_id'] == pitcher_id]
    print(p_logs['player_id'].tolist()[0])
    proj_acc = pitcher_dict(pitcher_id, steamer_pitchers)
    baseline = copy.deepcopy(proj_acc)
    all_projections = []
    #hackery as pitcher logs do not individually log non-hr hits
    all_hits = baseline['single'] + baseline['double'] + baseline['triple']
    s_ratio = baseline['single'] / all_hits
    d_ratio = baseline['double'] / all_hits
    t_ratio = baseline['triple'] / all_hits

    p_const = 450
    totals = dict(pa=0, k=0, bb=0, hbp=0, hr=0, single=0, double=0, triple=0)
    for ix, stat_line in p_logs.iterrows():
        try:
            home_team = games[games['key'] == stat_line['game_id']].iloc[0]['home']
        except:
            print('Game',stat_line['game_id'],'doesn\'t exist. Continuing')
            continue
        acc = copy.deepcopy(proj_acc)
        acc['date'] = stat_line['game_date']
        all_projections.append(acc)
        try:
            temp_hit_adj = 0.8416988 + (1.025144 - 0.8416988)/(1 + (temps[acc['date']][home_team]/92.86499) ** 4.391434)
            temp_hr_adj = 0.3639859 + (1.571536 - 0.3639859)/(1 + (temps[acc['date']][home_team]/67.64016) ** 1.381388)
        except:
            print(games[games['key'] == stat_line['game_id']].iloc[0])
            temp_hit_adj = 1
            temp_hr_adj = 1
        pf = park_factors[park_factors['Team'] == home_team].to_dict('records')[0]
        totals['pa'] = totals['pa'] + stat_line['tbf']
        totals['k'] = totals['k'] + stat_line['so']
        totals['bb'] = totals['bb'] + stat_line['bb']
        totals['hbp'] = totals['hbp'] + stat_line['hb']
        totals['hr'] = totals['hr'] + stat_line['hr']
        totals['triple'] = totals['triple'] + (stat_line['h'] - stat_line['hr']) * t_ratio
        totals['double'] = totals['double'] + (stat_line['h'] - stat_line['hr']) * d_ratio
        totals['single'] = totals['single'] + (stat_line['h'] - stat_line['hr']) * s_ratio
        proj_acc['k'] = accumulator_conditional(totals, proj_acc['k'], 'k', 'pa', 70)
        proj_acc['bb'] = accumulator_conditional(totals, proj_acc['bb'], 'bb', 'pa', 170)
        proj_acc['hbp'] = accumulator_conditional(totals, proj_acc['hbp'], 'hbp', 'pa', 640)
        proj_acc['hr'] = accumulator_conditional(totals, proj_acc['hr'], 'hr', 'pa', 1320)
        proj_acc['triple'] = accumulator_conditional(totals, proj_acc['triple'], 'triple', 'pa', 1450)
        proj_acc['double'] = accumulator_conditional(totals, proj_acc['double'], 'double', 'pa', 1450)
        proj_acc['single'] = accumulator_conditional(totals, proj_acc['single'], 'single', 'pa', 670)
    proj_acc['date'] = (datetime.strptime(all_projections[-1]['date'], '%Y-%m-%d') + timedelta(1)).strftime('%Y-%m-%d')
    all_projections.append(proj_acc)
    vL_projections = steamer_pitchers[steamer_pitchers['split'] == 'vL']
    vR_projections = steamer_pitchers[steamer_pitchers['split'] == 'vR']
    vL_base = pitcher_dict(pitcher_id, vL_projections)
    vR_base = pitcher_dict(pitcher_id, vR_projections)
    acc = []
    keys = ['k','bb','hbp','hr','triple','double','single']
    throws = vR_base['throws']
    for ros_proj in all_projections:
        transformations = { key: ros_proj[key]/baseline[key] for key in keys }
        vL = { 'vL_'+key: vL_base[key] * transformations[key] for key in keys }
        vR = { 'vR_'+key: vR_base[key] * transformations[key] for key in keys }
        combined = {**vL, **vR}
        combined['date'] = ros_proj['date']
        combined['mlb_id'] = pitcher_id
        combined['throws'] = throws
        acc.append(combined)
    return pd.DataFrame(acc)

def update_temperatures():
    lineups = pd.read_csv(os.path.join('data','lineups','lineups_{}.csv'.format(year)))
    temperature_dict = {}
    for ix, row in lineups.iterrows():
        if team_codes[row['name']] != row['key'].split('-')[1].split('mlb')[0]:
            continue
        home_team = row['name']
        date = row['date']
        temp = row['temp']
        if date not in temperature_dict:
            temperature_dict[date] = {}
        temperature_dict[date][home_team] = temp
    with open(os.path.join('data','temps.json'), 'w') as outfile:
        json.dump(temperature_dict, outfile)

if __name__ == '__main__':
    update_temperatures()
    pitcher_logs = pd.read_csv(os.path.join('data','player_logs','pitchers_{}.csv'.format(year)))
    steamer_pitchers = pd.read_csv(os.path.join('data','steamer', 'steamer_pitchers_{}_split.csv'.format(year)))
    player_ids = list(set(pitcher_logs['player_id'].tolist()))
    steamer_ids = list(set(steamer_pitchers['mlbamid'].tolist()))
    all_pitchers = []
    for ix, player_id in enumerate(player_ids):
        if ix%25 ==0:
            print(ix,'/',len(player_ids))
        if player_id not in steamer_ids:
            print('No splits for pitcher', player_id, 'will continue')
            continue
        proj = update_pitcher_projections(player_id, pitcher_logs, steamer_pitchers)
        all_pitchers.append(proj)
    df = pd.concat(all_pitchers).set_index(['mlb_id','date'])
    df.to_csv(os.path.join('data','projections','pitchers_{}.csv'.format(year)))

    hitter_logs = pd.read_csv(os.path.join('data','player_logs','batters_{}.csv'.format(year)))
    steamer_batters = pd.read_csv(os.path.join('data','steamer', 'steamer_hitters_{}_split.csv'.format(year)))
    player_ids = list(set(hitter_logs['player_id'].tolist()))
    steamer_ids = list(set(steamer_batters['mlbamid'].tolist()))
    all_hitters = []
    for player_id in player_ids:
        if player_id not in steamer_ids:
            print('No splits for batter', player_id, 'will continue')
            continue
        all_hitters.append(update_batter_projections(player_id, hitter_logs, steamer_batters))
    df = pd.concat(all_hitters).set_index(['mlb_id','date'])
    df.to_csv(os.path.join('data','projections','hitters_{}.csv'.format(year)))
