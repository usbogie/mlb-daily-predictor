import pandas as pd
import random
import json
import sys
import os

year = 2018

steamer_batters = pd.read_csv(os.path.join('data','steamer', 'steamer_hitters_{}.csv'.format(year)))
park_factors = pd.read_csv(os.path.join('data','park_factors_general.csv'))
hitter_logs = pd.read_csv(os.path.join('data','player_logs','batters_{}.csv'.format(year)))
games = pd.read_csv(os.path.join('data','games','games_{}.csv'.format(year)))

def update_batter_projections(batter_id):
    batter_logs = hitter_logs.loc[hitter_logs['player_id'] == batter_id]
    batter_projections = steamer_batters.loc[steamer_batters['mlbamid'] == batter_id].to_dict('records')[0]
    projections_accumulator = dict(
        k = batter_projections['K'] / batter_projections['PA'],
        bb = batter_projections['BB'] / batter_projections['PA'],
        hbp = batter_projections['HBP'] / batter_projections['PA'],
        hr = batter_projections['HR'] / batter_projections['PA'],
        triple = batter_projections['3B'] / batter_projections['PA'],
        double = batter_projections['2B'] / batter_projections['PA'],
        single = batter_projections['1B'] / batter_projections['PA'],
    )
    print(projections_accumulator)
    for ix, stat_line in batter_logs.iterrows():
        game = games.loc[games['key'] == stat_line['game_id']]
        home_team = game.iloc[0]['home']
        pf = park_factors[park_factors['Team'] == home_team].to_dict('records')[0]
        pa = stat_line['tpa']
        projections_accumulator['k'] = ((projections_accumulator['k'] * (650 - pa)) + stat_line['so']) / 650
        projections_accumulator['bb'] = ((projections_accumulator['bb'] * (650 - pa)) + stat_line['bb']) / 650
        projections_accumulator['hbp'] = ((projections_accumulator['hbp'] * (650 - pa)) + stat_line['hbp']) / 650
        projections_accumulator['hr'] = ((projections_accumulator['hr'] * (650 - pa)) + stat_line['hr'] / (pf['HR'] / 100)) / 650
        projections_accumulator['triple'] = ((projections_accumulator['triple'] * (650 - pa)) + stat_line['t'] / (pf['3B'] / 100)) / 650
        projections_accumulator['double'] = ((projections_accumulator['double'] * (650 - pa)) + stat_line['d'] / (pf['2B'] / 100)) / 650
        projections_accumulator['single'] = ((projections_accumulator['single'] * (650 - pa)) + (stat_line['h'] - stat_line['hr'] - stat_line['t'] - stat_line['d']) / (pf['1B'] / 100)) / 650
    print(projections_accumulator)

if __name__ == '__main__':
    update_batter_projections(605412)
