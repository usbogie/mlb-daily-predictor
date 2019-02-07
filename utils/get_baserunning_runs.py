

def calculate(lineup, steamer, manifest):
    total_runs = 0
    pitcher_fantasylabs_id = int(lineup['10_id'])
    for i in range(1,10):
        batter_name = lineup['{}_name'.format(str(i))]
        batter_fantasylabs_id = int(lineup['{}_id'.format(str(i))])
        if batter_fantasylabs_id == pitcher_fantasylabs_id:
            total_runs = total_runs + 0
            continue

        player_id = manifest[manifest['fantasy_labs'] == batter_fantasylabs_id].iloc[0]['mlb_id']
        player = steamer[steamer['mlbamid'] == player_id].iloc[0]
        total_runs = total_runs + (player['BaseRunning'] / player['G'])
    return total_runs * 162
