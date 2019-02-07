from datetime import datetime
import pandas as pd

avg_reliever_siera = 3.8

opener_innings = {
    '2018-04-29': {
        542882: (3, 'bp')
    },
    '2018-05-04': {
        552640: (2, 642232)
    },
    '2018-05-12': {
        542882: (3, 'bp')
    },
    '2018-05-19': {
        489265: (1, 642232)
    },
    '2018-05-20': {
        489265: (1.5, 607455)
    },
    '2018-05-24': {
        572998: (2, 'bp')
    },
    '2018-05-25': {
        489265: (1, 642232)
    },
    '2018-05-26': {
        592773: (2, 607455)
    },
    '2018-05-27': {
        489265: (1, 643493)
    },
    '2018-05-31': {
        592773: (2, 642232)
    },
    '2018-06-01': {
        518397: (1.5, 642701),
        489265: (1, 643493)
    },
    '2018-06-07': {
        543339: (1, 520980),
        592773: (2, 643493)
    },
    '2018-06-12': {
        592773: (2, 643493)
    },
    '2018-06-16': {
        592773: (2, 642232)
    },
    '2018-06-18': {
        592773: (2, 542882)
    },
    '2018-06-22': {
        592773: (2, 642232)
    },
    '2018-06-23': {
        608652: (3, 'bp')
    },
    '2018-06-24': {
        460283: (2, 'bp'),
        542882: (3, 'bp')
    },
    '2018-06-28': {
        592773: (2, 642232)
    },
    '2018-06-30': {
        592773: (2, 573064)
    },
    '2018-07-04': {
        542882: (3, 'bp')
    },
    '2018-07-06': {
        592773: (2, 'bp')
    },
    '2018-07-10': {
        592773: (2, 'bp')
    },
    '2018-07-11': {
        621056: (1, 'bp')
    },
    '2018-07-15': {
        612434: (3, 'bp'),
        592773: (2, 'bp')
    },
    '2018-07-21': {
        592773: (2, 642232)
    },
    '2018-07-23': {
        608601: (2, 448802),
        621056: (2, 542882),
    },
    '2018-07-25': {
        592773: (2, 'bp')
    },
    '2018-07-26': {
        621056: (2, 642232),
    },
    '2018-07-28': {
        446099: (2, 'bp'),
        592773: (2, 656222)
    },
    '2018-07-31': {
        592773: (2, 642232)
    },
    '2018-08-02': {
        461325: (1, 623434),
        621056: (2, 656222),
    },
    '2018-08-03': {
        592773: (2, 'bp')
    },
    '2018-08-05': {
        621056: (2, 642232),
    },
    '2018-08-07': {
        545363: (1, 571656)
    },
    '2018-08-08': {
        592773: (2, 656222)
    },
    '2018-08-09': {
        621056: (2, 630023),
    },
    '2018-08-11': {
        592773: (2, 'bp')
    },
    '2018-08-12': {
        518566: (2, 'bp')
    },
    '2018-08-14': {
        621056: (2, 656222),
    },
    '2018-08-16': {
        518566: (2, 'bp')
    },
    '2018-08-17': {
        592773: (2, 630023)
    },
    '2018-08-19': {
        571656: (1, 621385),
        650895: (1.5, 656222)
    },
    '2018-08-20': {
        621056: (2, 642232),
    },
    '2018-08-21': {
        502748: (1.5, 664285),
        543883: (2, 446321)
    },
    '2018-08-22': {
        592773: (2, 630023)
    },
    '2018-08-24': {
        650895: (1.5, 656222)
    },
    '2018-08-28': {
        598287: (1, 518566),
        592773: (2, 630023)
    },
    '2018-08-29': {
        650895: (1.5, 656222)
    },
    '2018-09-01': {
        521230: (1.5, 'bp')
    },
    '2018-09-02': {
        622382: (2, 641793),
        650895: (1.5, 642232)
    },
    '2018-09-03': {
        605488: (2, 642558),
        592773: (2, 630023)
    },
    '2018-09-04': {
        543507: (1, 640464),
        521230: (1, 596043),
        592773: (2, 656222)
    },
    '2018-09-07': {
        521230: (1, 605135)
    },
    '2018-09-08': {
        650895: (1.5, 642232)
    },
    '2018-09-09': {
        605488: (2, 642558),
        592773: (2, 630023)
    },
    '2018-09-10': {
        650895: (1.5, 656222)
    },
    '2018-09-11': {
        462382: (1.5, 598287),
        608648: (2, 640464)
    },
    '2018-09-12': {
        521230: (1, 596043)
    },
    '2018-09-13': {
        622382: (2, 624427)
    },
    '2018-09-14': {
        656814: (1.5, 642231),
        592712: (1, 622795),
        650895: (1.5, 642232)
    },
    '2018-09-15': {
        592222: (1, 642558),
        521230: (1, 605135),
        592773: (2, 630023)
    },
    '2018-09-16': {
        650895: (1.5, 'bp')
    },
    '2018-09-17': {
        623465: (2, 543219),
        622382: (1, 640464)
    },
    '2018-09-18': {
        521230: (1, 596043),
        542882: (3, 'bp')
    },
    '2018-09-19': {
        622382: (1, 624427),
        650895: (1.5, 642232)
    },
    '2018-09-20': {
        592773: (2, 630023)
    },
    '2018-09-21': {
        592712: (1, 642558),
        521230: (1, 605135),
        650895: (1.5, 656222)
    },
    '2018-09-24': {
        543359: (0.5, 642547),
        656547: (1, 543243),
        650895: (1.5, 642232)
    },
    '2018-09-25': {
        622382: (1, 640464)
    },
    '2018-09-26': {
        605240: (1, 'bp'),
        606965: (2, 'bp'),
        592773: (2, 630023)
    },
    '2018-09-27': {
        621289: (0.5, 643493),
        622382: (1, 624427)
    },
    '2018-09-28': {
        664682: (0.5, 'bp'),
        642152: (1, 571666),
        595191: (4, 'bp')
    },
    '2018-09-29': {
        521230: (1, 502239)
    },
    '2018-09-30': {
        592773: (1, 'bp')
    }
}

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
            print(name)
            return None
    player_id = player_ids.iloc[0]['mlb_id']
    player = projections[projections['mlb_id'] == player_id]

    dates = player['date'].tolist()
    if date not in dates:
        try:
            print('Date not in projection dates')
            target = nearest([datetime.strptime(d, '%Y-%m-%d') for d in dates], datetime.strptime(date, '%Y-%m-%d'))
            target = target.strftime('%Y-%m-%d')
        except:
            print(name)
            return None
    else:
        target = date
    player = player[player['date'] == target].to_dict('records')[0]
    return player

def calculate(lineup, date, manifest, projections):
    starter_name = lineup['10_name']
    print(starter_name, end=" ")
    fantasylabs_id = int(lineup['10_id'])

    pitcher = get_player(fantasylabs_id, starter_name, date, manifest, projections)
    if pitcher is None:
        print(pitcher)
        return None
    # print(pitcher)
    if date in opener_innings and pitcher['mlb_id'] in opener_innings[date]:
        innings, reliever_id = opener_innings[date][pitcher['mlb_id']]
        if reliever_id == 'bp':
            runs_allowed = ((pitcher['siera'] / 9) * innings) + ((avg_reliever_siera / 9) * (9-innings))
        else:
            reliever = projections[(projections['date'] == date) & (projections['mlb_id'] == reliever_id)].to_dict('records')[0]
            runs_allowed = ((pitcher['siera'] / 9) * innings) \
                            + ((reliever['siera'] / 9) * 4.5) \
                            + ((avg_reliever_siera / 9) * (9-innings-4.5))
    else:
        runs_allowed = (pitcher['siera'] / 9) * 5.5 + (avg_reliever_siera / 9) * 3.5
    # print(runs_allowed)
    return runs_allowed * 162
