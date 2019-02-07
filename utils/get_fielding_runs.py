

def calculate(dh, pitcher_id, player_ids, steamer):
    acc = 0
    i = 0
    fielders = steamer[(steamer['mlbamid'].isin(player_ids)) &
                       (steamer['split'] == 'overall') &
                       (steamer['pn'] == 1)]
    positions = ['C', '1B', '2B', 'SS', '3B', 'LF', 'CF', 'RF']
    if dh and pitcher_id not in player_ids:
        positions = positions + ['DH']

    position_dict = {}
    position_importance = {
        "1B": 0.95,
        "2B": 0.01,
        "SS": 1.04,
        "3B": 0.98,
        "LF": 1.00,
        "CF": 1.04,
        "RF": 1.04,
    }
    for position in positions:
        fielders = fielders.assign(f = (fielders['g'+position] + fielders['gUIF'] + fielders['gUOF'])/fielders['G']).sort_values('f').drop('f', axis=1).iloc[::-1]
        try:
            fielder = fielders.to_dict('records')[0]
        except:
            print(fielder)
            print(fielders)
            sys.exit
        if position != 'C' and position != 'DH':
            try:
                uzr = fielder['UZR'] / sum([fielder['g'+pos] for pos in ['1B', '2B', 'SS', '3B', 'LF', 'CF', 'RF', 'UIF', 'UOF']])
            except:
                uzr = 0
            uzr_adj = uzr * position_importance[position]
            acc = acc + uzr_adj
        position_dict[position] = fielder['fullname']
        fielders = fielders.iloc[1:]
    # print(acc)
    return acc * 162
