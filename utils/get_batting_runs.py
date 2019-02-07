from datetime import datetime
import pandas as pd

pa_by_order = {
    1: 4.65,
    2: 4.55,
    3: 4.43,
    4: 4.33,
    5: 4.24,
    6: 4.13,
    7: 4.01,
    8: 3.90,
    9: 3.77,
}

r_pa = {
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
}

def nearest(items, pivot):
    return min(items, key=lambda x: abs(x - pivot))

def player_in_fantasy_labs(name, id, manifest):
    players = manifest[(manifest['mlb_name'] == name)]
    ids = players['mlb_id'].unique().tolist()
    print(players)
    if len(ids) > 0:
        if len(ids) > 1:
            print(ids)
            print("DUPLICATE something is wrong\n",players)
            ix = int(input("Which player is actually playing? => "))
            player = players.iloc[[ix-1]]
        else:
            player = players.iloc[[0]]
        print("NEW PLAYER! Matching", name, "to", player['mlb_name'])
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
            return None

    player_id = player_ids.iloc[0]['mlb_id']
    player = projections[projections['mlb_id'] == player_id]

    dates = player['date'].tolist()
    if date not in dates:
        try:
            print(name)
            target = nearest([datetime.strptime(d, '%Y-%m-%d') for d in dates], datetime.strptime(date, '%Y-%m-%d'))
            target = target.strftime('%Y-%m-%d')
        except:
            return None
    else:
        target = date
    player = player[player['date'] == target].to_dict('records')[0]
    return player

def calculate(lineup, date, manifest, projections):
    total_runs = 0
    pitcher_fantasylabs_id = int(lineup['10_id'])
    for i in range(1,10):
        fantasylabs_id = int(lineup['{}_id'.format(str(i))])
        batter_name = lineup['{}_name'.format(str(i))]
        if fantasylabs_id == pitcher_fantasylabs_id:
            total_runs = total_runs + ((-0.2 / 100) * r_pa[date[:4]] * pa_by_order[i])
            continue
        player = get_player(fantasylabs_id, batter_name, date, manifest, projections)
        if player is None:
            return None
        # print(player)
        total_runs = total_runs + ((player['wrcplus'] / 100) * r_pa[date[:4]] * pa_by_order[i])
    return total_runs * 162
