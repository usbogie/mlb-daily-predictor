from pybaseball import statcast
from scraper_utils import get_days_in_season, statcast_to_mlb
from datetime import datetime, timedelta
import pandas as pd
import os

year = 2015
games = pd.read_csv(os.path.join('..','data','games','games_{}.csv'.format(year)))

pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 200)

headers = ['game_pk', 'key', 'game_date', 'batter', 'pitcher', 'events', 'description', 'des',
           'pitch_type', 'release_speed', 'release_pos_x', 'release_pos_y', 'release_pos_z', 'release_spin_rate',
           'release_extension', 'effective_speed', 'p_throws', 'zone', 'stand','pitch_number',
           'type', 'bb_type', 'balls', 'strikes', 'pfx_x',
           'pfx_z', 'plate_x', 'plate_z', 'sv_id', 'vx0',
           'vy0', 'vz0', 'ax', 'ay', 'az', 'sz_top',
           'sz_bot', 'hit_distance_sc', 'launch_speed', 'launch_angle',
           # 'fielder_2', 'fielder_3', 'fielder_4','fielder_5', 'fielder_6', 'fielder_7', 'fielder_8', 'fielder_9',
           'estimated_ba_using_speedangle',
           'estimated_woba_using_speedangle', 'woba_value', 'woba_denom',
           'babip_value', 'iso_value', 'launch_speed_angle', 'at_bat_number']

keys_used = []

def get_game_key(row):
    try:
        key = games[games['gamePk'] == row['game_pk']]['key'].iloc[0]
    except:
        print(row['game_pk'], "not found")
        return None
    print(key)
    keys_used.append(key)
    return key

def get_statcast_day(day):
    print(day)
    end = (datetime.strptime(day, '%Y-%m-%d') + timedelta(1)).strftime('%Y-%m-%d')
    try:
        data = statcast(day, end)
    except:
        print("Failure to get stats. Trying again")
        data = statcast(day, end)
    games = data[data['game_date'] == day].groupby('game_pk')
    dfs = []
    for ix, game in games:
        # print(list(game[1]))
        key = get_game_key(game.iloc[0])
        if key is None:
            continue
        game['key'] = key
        df = game[headers].sort_values(['at_bat_number','pitch_number'])
        # print(df.head(5))
        dfs.append(df)
    keys_used = []
    if len(dfs) == 0:
        return None
    return pd.concat(dfs)

def get_statcast_year(year=2018):
    days = get_days_in_season(year)
    dfs = []
    for day in days:
        day_df = get_statcast_day(day)
        if day_df is not None:
            dfs.append(day_df)
        print(len(dfs))
    return pd.concat(dfs)

if __name__ == '__main__':
    year_df = get_statcast_year(year)
    csv_path = os.path.join('..','data','statcast','{}.csv'.format(year))
    year_df.to_csv(csv_path, index=False)
