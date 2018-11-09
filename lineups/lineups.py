import random
import math
from datetime import datetime
from update_projections import batter_dict, pitcher_dict

keys = ['single','double','triple','hr','k','hbp','bb']
avg_pitcher_stats = {'vL': {'pa': 5277, 'single': 0.0879, 'double': 0.015, 'triple': 0.0013, 'hr': 0.0051,
                            'bb': 0.0307, 'hbp': 0.003, 'k': 0.3843, 'bats': 'B'},
                     'vR': {'pa': 5277, 'single': 0.0879, 'double': 0.015, 'triple': 0.0013, 'hr': 0.0051,
                            'bb': 0.0307, 'hbp': 0.003, 'k': 0.3843, 'bats': 'B'},
                     'pos': 'SP', 'mlb_id': 'pitcher'}

def determine_reliever_2018(name, team):
    if name == 'Ryan Cook' and team == 'Seattle Mariners':
        return 475857
    elif name == 'Jose Castillo' and team == 'San Diego Padres':
        return 620454
    elif name == 'Will Smith' and team == 'San Francisco Giants':
        return 519293
    elif name == 'Luis Garcia' and team == 'Philadelphia Phillies':
        return 472610
    elif name == 'Edwin Diaz' and team == 'Seattle Mariners':
        return 621242
    elif name == 'Diego Castillo' and team == 'Tampa Bay Rays':
        return 650895
    elif name == 'Austin Davis' and team == 'Philadelphia Phillies':
        return 656354
    elif name == 'Richard Rodriguez' and team == 'Pittsburgh Pirates':
        return 593144
    elif name == 'Ricardo Rodriguez' and team == 'Texas Rangers':
        return 600965
    elif name == 'Cody Reed' and team == 'Cincinnati Reds':
        return 642003
    elif name == 'Luis Santos' and team == 'Toronto Blue Jays':
        return 608601
    elif name == 'Carlos Martinez' and team == 'St. Louis Cardinals':
        return 593372
    elif name == 'Aaron Brooks' and team == 'Oakland Athletics':
        return 605156
    elif name == 'Jose Fernandez' and team == 'Toronto Blue Jays':
        return 622774
    return False

def player_not_in_fantasy_labs(name, id, manifest):
    if id in manifest['fantasy_labs'].tolist():
        return
    players = manifest[(manifest['mlb_name'] == name)]
    ids = players['mlb_id'].unique().tolist()
    print(players)
    if len(ids) > 0:
        if len(ids) > 1:
            print("DUPLICATE something is wrong\n",players)
            ix = int(input("Which player is actually playing? => "))
            players = players.iloc[[ix-1]]
        else:
            try:
                players = players.iloc[[0]]
            except:
                return False
        players = players.to_dict('records')[0]
        print("NEW PLAYER! Matching", name, "to", players['mlb_name'])
        manifest.at[manifest.index[manifest['mlb_id'] == players['mlb_id']],'fantasy_labs'] = id
        print('Matched', id, "to", players['mlb_id'])
    else:
        print('Couldnt find {}. Giving average batter stats'.format(name))
        return False

def nearest(items, pivot):
    return min(items, key=lambda x: abs(x - pivot))

def get_stats(date, player_id, projections, steamer, player_dict, arg):
    player = projections[projections['mlb_id'] == player_id]
    if player.empty:
        player = steamer[steamer['mlbamid'] == player_id]
        if player.empty:
            print(player_id, 'player not in steamer')
            return False

        vL = player_dict(player_id, player[player['split'] == 'vL'])
        vR = player_dict(player_id, player[player['split'] == 'vR'])
        return dict(vL = vL, vR = vR, mlb_id = player_id)
    else:
        dates = player['date'].tolist()
        if date not in dates:
            target = nearest([datetime.strptime(d, '%Y-%m-%d') for d in dates], datetime.strptime(date, '%Y-%m-%d'))
            target = target.strftime('%Y-%m-%d')
        else:
            target = date
        player = player[player['date'] == target].to_dict('records')
        if len(player) == 2 and player[0]['mlb_id'] == player[1]['mlb_id']:
            player = player[1]
        elif len(player) > 1:
            print("Something wrong")
        else:
            player = player[0]

        #if 'throws' not in player.keys():
            #print(player)
        vL = { key: player['vL_'+key] for key in keys }
        vR = { key: player['vR_'+key] for key in keys }
        vL[arg], vR[arg] = player[arg], player[arg]
        vL['mlb_id'], vR['mlb_id'] = player['mlb_id'], player['mlb_id']
        return dict(vL = vL, vR = vR, mlb_id = player['mlb_id'])

def get_batting_stats(manifest, batter_projections, steamer_batters, lineup, date):
    lineup_stats = []

    for i in range(1,10):
        batter_name = lineup['{}_name'.format(str(i))]
        batter_fantasylabs_id = int(lineup['{}_id'.format(str(i))])
        pitcher_fantasylabs_id = int(lineup['10_id'])
        if batter_fantasylabs_id == pitcher_fantasylabs_id:
            lineup_stats.append(dict(avg_pitcher_stats))
            continue

        if player_not_in_fantasy_labs(batter_name, batter_fantasylabs_id, manifest) == False:
            return False

        player_id = manifest[manifest['fantasy_labs'] == batter_fantasylabs_id].iloc[0]['mlb_id']
        stats = get_stats(date, player_id, batter_projections, steamer_batters, batter_dict, 'bats')
        stats['pos'] = lineup['{}_pos'.format(str(i))]
        if not stats:
            return False
        lineup_stats.append(stats)
    return lineup_stats

def get_pitching_stats(manifest, pitcher_projections, all_relievers, steamer_pitchers, steamer_starters, lineup, date, test=False, bullpens=None):
    starter_name = lineup['10_name']
    starter_fantasylabs_id = int(lineup['10_id'])
    print(starter_name)

    if player_not_in_fantasy_labs(starter_name, starter_fantasylabs_id, manifest) == False:
        return False
    pitcher_id = manifest[manifest['fantasy_labs'] == starter_fantasylabs_id].iloc[0]['mlb_id']
    starting_pitcher = get_stats(date, pitcher_id, pitcher_projections, steamer_pitchers, pitcher_dict, 'throws')
    starting_pitcher['usage'], starting_pitcher['pos'] = 'SP', 'SP'
    starting_pitcher['GS'] = steamer_starters[steamer_starters['mlbamid'] == pitcher_id].iloc[0]['GS']
    starting_pitcher['start_IP'] = steamer_starters[steamer_starters['mlbamid'] == pitcher_id].iloc[0]['start_IP']
    pitchers = [starting_pitcher]

    if not test:
        closers = []
        relievers = all_relievers[lineup['name']]
        for name, info in relievers.items():
            reliever = manifest[(manifest['mlb_name'] == name)]
            ids = reliever['mlb_id'].unique().tolist()
            if len(ids) > 1:
                reliever_id = determine_reliever_2018(name, lineup['name'])
                if not reliever_id:
                    print("DUPLICATE something is wrong\n",reliever)
                    ix = int(input("Which player is actually playing? => "))
                    reliever_id = reliever.iloc[ix-1]['mlb_id']
            elif len(ids) > 0:
                reliever_id = ids[0]
            else:
                print('No pitcher matched', name)
                continue
            reliever = get_stats(date, reliever_id, pitcher_projections, steamer_pitchers, pitcher_dict, 'throws')
            if not reliever:
                continue
            reliever['usage'] = info[1]
            if 'CL' not in info:
                pitchers.append(reliever)
            else:
                closers.append(reliever)
        random.shuffle(closers)
        pitchers.extend(closers)
    else:
        game = bullpens[bullpens['key'] == lineup['key']].to_dict('records')[0]
        home_away = 'bp_away' if game['away'] == lineup['name'] else 'bp_home'
        all_pitchers = [game[col] for col in game if col.startswith(home_away)]
        all_pitchers = [int(pitcher) for pitcher in all_pitchers if str(pitcher) != 'nan']
        # remove starter
        all_pitchers.remove(pitcher_id)
        bp_df = steamer_starters[steamer_starters['mlbamid'].isin(all_pitchers)].sort_values(by=['start_IP'],ascending=False)
        relievers_list = bp_df.iloc[4:]['mlbamid'].tolist()
        dist = 1/len(relievers_list)
        for reliever in relievers_list:
            reliever = get_stats(date, reliever, pitcher_projections, steamer_pitchers, pitcher_dict, 'throws')
            if not reliever:
                continue
            reliever['usage'] = dist
            pitchers.append(reliever)
    return pitchers

def get_team_defense(lineup, fielders):
    acc = 0
    i = 0
    catchers = [p for p in lineup if p['pos'] == 'C']
    if len(catchers) != 1:
        ratio_high = 0
        most_likely_catcher = None
        for c in catchers:
            catcher = fielders[fielders['mlbamid'] == c['mlb_id']].to_dict('records')[0]
            catcher_ratio = catcher['gC'] / math.ceil(catcher['G'])
            if catcher_ratio >= ratio_high:
                ratio_high = catcher_ratio
                most_likely_catcher = c['mlb_id']
    else:
        most_likely_catcher = catchers[0]['mlb_id']

    for player in lineup:
        pos = player['pos']
        id = player['mlb_id']
        if pos == 'SP' or (pos == 'C' and id == most_likely_catcher):
            continue
        i = i + 1
        fielder = fielders[fielders['mlbamid'] == id].to_dict('records')[0]
        uzr = fielder['UZR'] / fielder['G']
        acc = acc + uzr
    if i < 7:
        print('Something wrong, not enough fielders')
        sys.exit()
    return acc / 3 + 1
