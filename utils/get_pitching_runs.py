from datetime import datetime
import pandas as pd
import numpy as np
import os, json

r_g = {
    "2018": 4.45,
    "2017": 4.65,
    "2016": 4.48,
    "2015": 4.25,
}

woba_year = {
    "2018": 0.320,
    "2017": 0.326,
    "2016": 0.323,
    "2015": 0.318,
}

siera_year = {
    "2018": 3.59235961783155
}

opener_innings = {
    '2018-04-29': { 542882: (3, 'bp') },
    '2018-05-04': { 552640: (2, 642232) },
    '2018-05-12': { 542882: (3, 'bp') },
    '2018-05-19': { 489265: (1, 642232) },
    '2018-05-20': { 489265: (1.5, 607455) },
    '2018-05-24': { 572998: (2, 'bp') },
    '2018-05-25': { 489265: (1, 642232) },
    '2018-05-26': { 592773: (2, 607455) },
    '2018-05-27': { 489265: (1, 643493) },
    '2018-05-31': { 592773: (2, 642232) },
    '2018-06-01': { 518397: (1.5, 642701), 489265: (1, 643493) },
    '2018-06-05': { 458924: (1.5, 642232), },
    '2018-06-07': { 543339: (1, 520980), 592773: (2, 643493) },
    '2018-06-12': { 592773: (2, 643493) },
    '2018-06-16': { 592773: (2, 642232) },
    '2018-06-18': { 592773: (2, 542882) },
    '2018-06-22': { 592773: (2, 642232) },
    '2018-06-23': { 608652: (3, 'bp') },
    '2018-06-24': { 460283: (2, 'bp'), 542882: (3, 'bp') },
    '2018-06-28': { 592773: (2, 642232) },
    '2018-06-30': { 592773: (2, 573064) },
    '2018-07-04': { 542882: (3, 'bp') },
    '2018-07-06': { 592773: (2, 'bp') },
    '2018-07-10': { 592773: (2, 'bp') },
    '2018-07-11': { 621056: (1, 'bp') },
    '2018-07-15': { 612434: (3, 'bp'), 592773: (2, 'bp') },
    '2018-07-21': { 592773: (2, 642232) },
    '2018-07-23': { 608601: (2, 448802), 621056: (2, 542882), },
    '2018-07-25': { 592773: (2, 'bp') },
    '2018-07-26': { 621056: (2, 642232), }, '2018-07-28': { 446099: (2, 'bp'), 592773: (2, 656222) },
    '2018-07-31': { 592773: (2, 642232) },
    '2018-08-02': { 461325: (1, 623434), 621056: (2, 656222), },
    '2018-08-03': { 592773: (2, 'bp') },
    '2018-08-05': { 621056: (2, 642232), },
    '2018-08-07': { 545363: (1, 571656) },
    '2018-08-08': { 592773: (2, 656222) },
    '2018-08-09': { 621056: (2, 630023), },
    '2018-08-11': { 592773: (2, 'bp') },
    '2018-08-12': { 518566: (2, 'bp') },
    '2018-08-14': { 621056: (2, 656222), },
    '2018-08-16': { 518566: (2, 'bp') },
    '2018-08-17': { 592773: (2, 630023) },
    '2018-08-19': { 571656: (1, 621385), 650895: (1.5, 656222) },
    '2018-08-20': { 621056: (2, 642232), },
    '2018-08-21': { 502748: (1.5, 664285), 543883: (2, 446321) },
    '2018-08-22': { 592773: (2, 630023) },
    '2018-08-24': { 650895: (1.5, 656222) },
    '2018-08-28': { 598287: (1, 518566), 592773: (2, 630023) },
    '2018-08-29': { 650895: (1.5, 656222) },
    '2018-09-01': { 521230: (1.5, 'bp') },
    '2018-09-02': { 622382: (2, 641793), 650895: (1.5, 642232) },
    '2018-09-03': { 605488: (2, 642558), 592773: (2, 630023) },
    '2018-09-04': { 543507: (1, 640464), 521230: (1, 596043), 592773: (2, 656222) },
    '2018-09-07': { 521230: (1, 605135) },
    '2018-09-08': { 650895: (1.5, 642232) },
    '2018-09-09': { 605488: (2, 642558), 592773: (2, 630023) },
    '2018-09-10': { 650895: (1.5, 656222) },
    '2018-09-11': { 462382: (1.5, 598287), 608648: (2, 640464) },
    '2018-09-12': { 521230: (1, 596043) },
    '2018-09-13': { 622382: (2, 624427) },
    '2018-09-14': { 656814: (1.5, 642231), 592712: (1, 622795), 650895: (1.5, 642232) },
    '2018-09-15': { 592222: (1, 642558), 521230: (1, 605135), 592773: (2, 630023) },
    '2018-09-16': { 650895: (1.5, 'bp') },
    '2018-09-17': { 623465: (2, 543219), 622382: (1, 640464) },
    '2018-09-18': { 521230: (1, 596043), 542882: (3, 'bp') },
    '2018-09-19': { 622382: (1, 624427), 650895: (1.5, 642232) },
    '2018-09-20': { 592773: (2, 630023) },
    '2018-09-21': { 592712: (1, 642558), 521230: (1, 605135), 650895: (1.5, 656222) },
    '2018-09-24': { 543359: (0.5, 642547), 656547: (1, 543243), 650895: (1.5, 642232) },
    '2018-09-25': { 622382: (1, 640464) },
    '2018-09-26': { 605240: (1, 'bp'), 606965: (2, 'bp'), 592773: (2, 630023) },
    '2018-09-27': { 621289: (0.5, 643493), 622382: (1, 624427) },
    '2018-09-28': { 664682: (0.5, 'bp'), 642152: (1, 571666), 595191: (4, 'bp') },
    '2018-09-29': { 521230: (1, 502239) },
    '2018-09-30': { 592773: (1, 'bp') }
}

with open(os.path.join('data','team_starters.json')) as f:
    all_starters = json.load(f)

def nearest(items, pivot):
    return min(items, key=lambda x: abs(x - pivot))

def player_in_fantasy_labs(name, id, manifest):
    players = manifest[(manifest['mlb_name'] == name)]
    ids = players['mlb_id'].unique().tolist()
    if len(ids) > 0:
        if len(ids) > 1:
            print("DUPLICATE something is wrong\n",players)
            ix = int(input("Which player is actually playing? => "))
            player = players.iloc[[ix-1]]
        else:
            player = players.iloc[[0]]
        print("NEW PLAYER! Matching", name, "to", player['mlb_name'].iloc[0])
        manifest.at[manifest.index[manifest['mlb_id'] == player['mlb_id'].iloc[0]],'fantasy_labs'] = id
        print('Matched', id, "to", player['mlb_id'].iloc[0])
        return player
    else:
        print('Couldnt find', name)
        return pd.DataFrame()

def get_player(player_id, name, date, manifest, projections):
    player_ids = manifest[manifest['fantasy_labs'] == player_id]
    if len(player_ids) == 0:
        print(name, 'not in manifest, looking...')
        player_ids = player_in_fantasy_labs(name, player_id, manifest)
        if player_ids.empty:
            print(name)
            return None
    player_id = player_ids.iloc[0]['mlb_id']
    player = projections[projections['mlb_id'] == player_id]

    dates = player['date'].tolist()
    if date not in dates:
        try:
            if date < min(dates):
                print(name, 'does not have enough batters faced, skipping')
                return None
            print(date, name, 'date not in projection dates, getting backup')
            target = nearest([datetime.strptime(d, '%Y-%m-%d') for d in dates], datetime.strptime(date, '%Y-%m-%d'))
            target = target.strftime('%Y-%m-%d')
        except:
            print(name)
            return None
    else:
        target = date
    player = player[player['date'] == target].to_dict('records')[0]
    return player

def calculate(lineup, date, manifest, projections, steamer, bp):
    starter_name = lineup['10_name']
    print(starter_name, end=" ")
    fantasylabs_id = int(lineup['10_id'])

    pitcher = get_player(fantasylabs_id, starter_name, date, manifest, projections)
    if pitcher is None:
        return None

    bullpen_pitchers = [int(x) for x in list(map(list, bp.values))[0] if str(x) != 'nan']
    bullpen_siera = 0
    num_bp_pitchers = 0
    for bpitcher in bullpen_pitchers:
        if bpitcher == pitcher['mlb_id'] or bpitcher in all_starters[lineup['name']]:
            continue
        bpitcher_projections = projections[(projections['mlb_id'] == bpitcher)]
        dates = bpitcher_projections['date'].tolist()
        if date not in dates:
            try:
                target = nearest([datetime.strptime(d, '%Y-%m-%d') for d in dates], datetime.strptime(date, '%Y-%m-%d'))
                target = target.strftime('%Y-%m-%d')
            except:
                print('could not find reliever', bpitcher)
                continue
        else:
            target = date
        player = bpitcher_projections[(bpitcher_projections['date'] == target)].iloc[-1]
        bullpen_siera = bullpen_siera + player['siera']
        num_bp_pitchers = num_bp_pitchers + 1

    bp_siera = bullpen_siera / num_bp_pitchers
    if date in opener_innings and pitcher['mlb_id'] in opener_innings[date]:
        innings, reliever_id = opener_innings[date][pitcher['mlb_id']]
        if reliever_id == 'bp':
            siera = (pitcher['siera'] * innings + bp_siera * (9-innings)) / 9
        else:
            reliever = projections[(projections['date'] == date) & (projections['mlb_id'] == reliever_id)].to_dict('records')[0]
            siera = (pitcher['siera'] * innings + reliever['siera'] * (5.5-innings) + bp_siera * 3.5) / 9
    else:
        steamer_pitcher = steamer[steamer['mlbamid'] == pitcher['mlb_id']].iloc[0]
        if steamer_pitcher['start_IP'] == 0:
            innings = 4.5
        else:
            innings = steamer_pitcher['start_IP'] / steamer_pitcher['GS']
        siera = (pitcher['siera'] * innings + bp_siera * (9-innings)) / 9
    print(pitcher['siera'], bp_siera)
    return (siera/siera_year[date[:4]]) * r_g[date[:4]]
