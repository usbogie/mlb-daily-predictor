import random
from update_projections import batter_dict, pitcher_dict

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

keys = ['single','double','triple','hr','k','hbp','bb']
avg_pitcher_stats = {'vL': {'pa': 5277, 'single': 0.0879, 'double': 0.015, 'triple': 0.0013, 'hr': 0.0051,
                            'bb': 0.0307, 'hbp': 0.003, 'k': 0.3843, 'bats': 'B', 'mlb_id': 'pitcher'},
                     'vR': {'pa': 5277, 'single': 0.0879, 'double': 0.015, 'triple': 0.0013, 'hr': 0.0051,
                            'bb': 0.0307, 'hbp': 0.003, 'k': 0.3843, 'bats': 'B', 'mlb_id': 'pitcher'}}

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

def get_stats(date, id, projections, steamer, player_dict, arg):
    player = projections[projections['mlb_id'] == id]
    if player.empty:
        player = steamer[steamer['mlbamid'] == id]
        if player.empty:
            print(id, 'player not in steamer')
            sys.exit()

        vL = player_dict(id, player[player['split'] == 'vL'])
        vR = player_dict(id, player[player['split'] == 'vR'])
        return dict(vL = vL, vR = vR)
    else:
        dates = player['date'].tolist()
        target = date if date in dates else max(dates)
        player = player[player['date'] == target].to_dict('records')
        if len(player) == 2 and player[0]['mlb_id'] == player[1]['mlb_id']:
            player = player[1]
        elif len(player) > 1:
            print("Something wrong")
        else:
            player = player[0]

        vL = { key: player['vL_'+key] for key in keys }
        vR = { key: player['vL_'+key] for key in keys }
        vL[arg], vR[arg] = player[arg], player[arg]
        vL['mlb_id'], vR['mlb_id'] = player['mlb_id'], player['mlb_id']
        return dict(vL = vL, vR = vR)

def get_batting_stats(manifest, batter_projections, steamer_batters, lineup, date):
    lineup_stats = []

    for i in range(1,10):
        batter_name = lineup['{}_name'.format(str(i))]
        batter_fantasylabs_id = int(lineup['{}_id'.format(str(i))])
        pitcher_fantasylabs_id = int(lineup['10_id'])
        if batter_fantasylabs_id == pitcher_fantasylabs_id:
            print(batter_name, "is probably a pitcher, given avg pitcher stats")
            lineup_stats.append(dict(avg_pitcher_stats))
            continue

        if player_not_in_fantasy_labs(batter_name, batter_fantasylabs_id, manifest) == False:
            return False


        player_id = manifest[manifest['fantasy_labs'] == batter_fantasylabs_id].iloc[0]['mlb_id']
        stats = get_stats(date, player_id, batter_projections, steamer_batters, batter_dict, 'bats')
        lineup_stats.append(stats)
    return lineup_stats

def get_pitching_stats(manifest, pitcher_projections, all_relievers, steamer_pitchers, steamer_starters, lineup, date, test=False):
    starter_name = lineup['10_name']
    starter_fantasylabs_id = int(lineup['10_id'])
    print(starter_name)

    if player_not_in_fantasy_labs(starter_name, starter_fantasylabs_id, manifest) == False:
        return False
    pitcher_id = manifest[manifest['fantasy_labs'] == starter_fantasylabs_id].iloc[0]['mlb_id']
    starting_pitcher = get_stats(date, pitcher_id, pitcher_projections, steamer_pitchers, pitcher_dict, 'throws')
    starting_pitcher['usage'] = 'SP'
    pitchers = [starting_pitcher]
    pitchers[0]['vL']['GS'] = steamer_starters[steamer_starters['mlbamid'] == pitchers[0]['vL']['mlb_id']].iloc[0]['GS']
    pitchers[0]['vL']['start_IP'] = steamer_starters[steamer_starters['mlbamid'] == pitchers[0]['vL']['mlb_id']].iloc[0]['start_IP']

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
            reliever['usage'] = info[1]
            if 'CL' not in info:
                pitchers.append(reliever)
            else:
                closers.append(reliever)
        random.shuffle(closers)
        pitchers.extend(closers)
    else:
        game = bullpens[bullpens['key'] == lineup['key']]
        if game.iloc[0]['away'] == lineup['name']:
            all_pitchers = [game.iloc[0][col] for col in game if col.startswith('bp_away')]
        else:
            all_pitchers = [game.iloc[0][col] for col in game if col.startswith('bp_home')]
        all_pitchers = [int(pitcher) for pitcher in all_pitchers if str(pitcher) != 'nan']
        # remove starter
        all_pitchers.remove(starter_fantasylabs_id)
        bp_df = steamer_starters[steamer_starters['mlbamid'].isin(all_pitchers)].sort_values(by=['start_IP'],ascending=False)
        relievers_list = bp_df.iloc[4:]['mlbamid'].tolist()
        dist = 1/len(relievers_list)
        relief = []
        for reliever in relievers_list:
            reliever = get_stats(date, reliever, pitcher_projections, steamer_pitchers, pitcher_dict, 'throws')
            reliever['usage'] = dist
            relief.append(reliever)
        random.shuffle(relief)
        pitchers.extend(relief)
    return pitchers
