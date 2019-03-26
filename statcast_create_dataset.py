import pandas as pd
import numpy as np
import os
import copy
from datetime import datetime
import batter_expected_stats, pitcher_expected_stats

year = 2018
statcast_logs = pd.read_csv(os.path.join('data','statcast','{}.csv'.format(year)))
steamer_pitchers = pd.read_csv(os.path.join('data','steamer', 'steamer_pitchers_{}_split.csv'.format(year)))
steamer_pitchers2 = pd.read_csv(os.path.join('data','steamer', 'steamer_pitchers_{}.csv'.format(year)))
steamer_batters_split = pd.read_csv(os.path.join('data','steamer', 'steamer_hitters_{}_split.csv'.format(year)))

pd.set_option('display.max_rows', 500)

def get_stat_acc():
    return dict(
        whiffs = 0,opitches = 0,zpitches = 0,pitches = 0,oswings = 0,
        zswings = 0,swings = 0,ocontacts = 0,zcontacts = 0,contacts = 0,
        firststrikes = 0,strikeslooking = 0,fouls = 0,plateappearances = 0,
        xwOBA = 0,xwOBA_denom = 0,wOBA = 0,wOBA_denom = 0,ballsinplay = 0,
        barrels = 0,flyballs = 0,popups = 0,groundballs = 0,linedrives = 0,
        strikeouts = 0,walks = 0,hbp = 0,hr = 0,
    )

def is_strike(row):
    return row['zone'] in range(1,10)
    # return (row['plate_x'] <= 0.83 and row['plate_x'] >= -0.83 \
    #     and row['plate_z'] <= row['sz_top'] + 0.02\
    #     and row['plate_z'] >= row['sz_bot'] - 0.02)

def analyze_pitch(row, stat_acc):
    if row['pitch_number'] == 1 and ('strike' in row['description'] \
            or 'foul' in row['description'] or 'hit' in row['description'] \
            or row['description'] == 'missed_bunt' or row['description'] == 'swinging_pitchout'):
        stat_acc['firststrikes'] = stat_acc['firststrikes'] + 1

    if row['description'] == 'called_strike' or row['description'] == 'pitchout' \
            or row['description'] == 'hit_by_pitch' or row['description'] == 'ball' \
            or row['description'] == 'blocked_ball':
        stat_acc['pitches'] = stat_acc['pitches'] + 1
        if row['description'] == 'hit_by_pitch':
            stat_acc['hbp'] = stat_acc['hbp'] + 1

        if is_strike(row):
            stat_acc['zpitches'] = stat_acc['zpitches'] + 1
            stat_acc['strikeslooking'] = stat_acc['strikeslooking'] + 1
        else:
            stat_acc['opitches'] = stat_acc['opitches'] + 1
    elif row['description'] == 'swinging_strike' or row['description'] == 'swinging_strike_blocked' \
            or row['description'] == 'swinging_pitchout' or row['description'] == 'foul_tip' \
            or row['description'] == 'missed_bunt':
        stat_acc['pitches'] = stat_acc['pitches'] + 1
        stat_acc['swings'] = stat_acc['swings'] + 1
        stat_acc['whiffs'] = stat_acc['whiffs'] + 1
        if is_strike(row):
            stat_acc['zpitches'] = stat_acc['zpitches'] + 1
            stat_acc['zswings'] = stat_acc['zswings'] + 1
        else:
            stat_acc['opitches'] = stat_acc['opitches'] + 1
            stat_acc['oswings'] = stat_acc['oswings'] + 1
    elif row['description'] == 'foul' or row['description'] == 'foul_bunt' \
            or row['description'] == 'foul_pitchout' or row['description'] == 'hit_into_play' \
            or row['description'] == 'hit_into_play_no_out' or row['description'] == 'hit_into_play_score':
        stat_acc['pitches'] = stat_acc['pitches'] + 1
        stat_acc['swings'] = stat_acc['swings'] + 1
        stat_acc['contacts'] = stat_acc['contacts'] + 1
        if 'foul' in row['description']:
            stat_acc['fouls'] = stat_acc['fouls'] + 1

        if is_strike(row):
            stat_acc['zpitches'] = stat_acc['zpitches'] + 1
            stat_acc['zswings'] = stat_acc['zswings'] + 1
            stat_acc['zcontacts'] = stat_acc['zcontacts'] + 1
        else:
            stat_acc['opitches'] = stat_acc['opitches'] + 1
            stat_acc['oswings'] = stat_acc['oswings'] + 1
            stat_acc['ocontacts'] = stat_acc['ocontacts'] + 1

    if row['events'] == 'field_out' or row['events'] == 'fielders_choice' \
            or row['events'] == 'fielders_choice_out' or row['events'] == 'field_error' \
            or row['events'] == 'force_out' or row['events'] == 'double_play' \
            or row['events'] == 'triple_play' or row['events'] == 'grounded_into_double_play' \
            or row['events'] == 'sac_fly_double_play' or row['events'] == 'sac_fly' \
            or row['events'] == 'home_run' or row['events'] == 'triple' \
            or row['events'] == 'double' or row['events'] == 'single':
        stat_acc['ballsinplay'] = stat_acc['ballsinplay'] + 1

        if row['bb_type'] == 'ground_ball':
            stat_acc['groundballs'] = stat_acc['groundballs'] + 1
        elif row['bb_type'] == 'line_drive':
            stat_acc['linedrives'] = stat_acc['linedrives'] + 1
        elif row['bb_type'] == 'fly_ball':
            stat_acc['flyballs'] = stat_acc['flyballs'] + 1
        elif row['bb_type'] == 'popup':
            stat_acc['popups'] = stat_acc['popups'] + 1

        if row['events'] == 'home_run':
            stat_acc['hr'] = stat_acc['hr'] + 1

        if row['launch_speed_angle'] == 6:
            stat_acc['barrels'] = stat_acc['barrels'] + 1

        if pd.isnull(row['woba_denom']):
            # something wrong, need to dig deeper, but for now just give simple fallback
            stat_acc['xwOBA'] = stat_acc['xwOBA'] + 0
            stat_acc['wOBA'] = stat_acc['wOBA'] + row['woba_value']

            stat_acc['xwOBA_denom'] = stat_acc['xwOBA_denom'] + 1
            stat_acc['wOBA_denom'] = stat_acc['wOBA_denom'] + 1
        else:
            stat_acc['xwOBA'] = stat_acc['xwOBA'] + row['estimated_woba_using_speedangle']
            stat_acc['wOBA'] = stat_acc['wOBA'] + row['woba_value']

            stat_acc['xwOBA_denom'] = stat_acc['xwOBA_denom'] + row['woba_denom']
            stat_acc['wOBA_denom'] = stat_acc['wOBA_denom'] + row['woba_denom']
        stat_acc['plateappearances'] = stat_acc['plateappearances'] + 1
    elif row['events'] == 'hit_by_pitch' or row['events'] == 'strikeout' \
            or row['events'] == 'strikeout_double_play' or row['events'] == 'walk':
        # stat_acc['xwOBA'] = stat_acc['xwOBA'] + row['woba_value']
        stat_acc['wOBA'] = stat_acc['wOBA'] + row['woba_value']
        stat_acc['wOBA_denom'] = stat_acc['wOBA_denom'] + row['woba_denom']
        stat_acc['plateappearances'] = stat_acc['plateappearances'] + 1
        if row['events'] == 'strikeout' \
                or row['events'] == 'strikeout_double_play':
            stat_acc['strikeouts'] = stat_acc['strikeouts'] + 1
        elif row['events'] == 'walk':
            stat_acc['walks'] = stat_acc['walks'] + 1
    return stat_acc

def generate_batter_stats(batters):
    k_scaler, k_lm = batter_expected_stats.get_xk_regression(year)
    bb_scaler, bb_lm = batter_expected_stats.get_xbb_regression(year)
    daily_projections = []
    for ix, mlb_id in enumerate(batters):
        print(mlb_id, str(ix) + '/' + str(len(batters)))
        logs = statcast_logs[statcast_logs['batter'] == mlb_id]
        if logs.empty:
            print("Empty logs for", mlb_id)
            continue
        logs = logs.sort_values(by='game_date')
        steamer = steamer_batters_split[
            (steamer_batters_split['mlbamid'] == mlb_id) &
            (steamer_batters_split['pn'] == 1) &
            (steamer_batters_split['split'] == 'overall')
        ]
        if steamer.empty:
            print("No steamer for", mlb_id)
            continue
        else:
            steamer = steamer.iloc[0]

        stat_acc = get_stat_acc()

        def get_projected_wobacon(steamer):
            if steamer.empty:
                return 0.370

            if 'wOBAcon' in steamer:
                return steamer['wOBAcon']
            else:
                woba = steamer['wOBA']
                tot = woba * steamer['PA']
                wobacon_numer = tot - (0.69 * steamer['NIBB']) - (0.72 * steamer['HBP'])
                wobacon_denom = steamer['PA'] - steamer['K'] - steamer['NIBB'] - steamer['HBP'] - steamer['SF']
                return wobacon_numer / wobacon_denom

        steamer_projection = dict(
            krate = steamer['K'] / (steamer['PA'] - steamer['IBB']),
            bbrate = steamer['NIBB'] / (steamer['PA'] - steamer['IBB']),
            hbprate = steamer['HBP'] / (steamer['PA'] - steamer['IBB']),
            hrrate = steamer['HR'] / (steamer['PA'] - steamer['IBB']),
            wobacon = get_projected_wobacon(steamer)
        )

        def calc_proj_woba():
            pa = stat_acc['plateappearances']
            if pa < 500:
                hbp = (steamer_projection['hbprate'] * (500 - pa) + stat_acc['hbp']) / 500
            else:
                hbp = stat_acc['hbp'] / pa

            if pa < 30:
                k = (steamer_projection['krate'] * (60 - pa) + stat_acc['strikeouts']) / 60
                bb = (steamer_projection['bbrate'] * (120 - pa) + stat_acc['walks']) / 120
            else:
                k_stats = dict(
                    Zswing = stat_acc['zswings']/stat_acc['zpitches'],
                    contact = stat_acc['contacts']/stat_acc['swings'],
                    SwStr = stat_acc['whiffs']/stat_acc['pitches'],
                    p_pa = stat_acc['pitches']/stat_acc['plateappearances'],
                    FlStr = stat_acc['fouls']/stat_acc['zpitches'],
                    LkStr = stat_acc['strikeslooking']/stat_acc['pitches'],
                )
                k_scaled = k_scaler.transform(pd.DataFrame([k_stats])[['Zswing', 'contact', 'SwStr', 'p_pa', 'FlStr', 'LkStr']])
                k_pred = k_lm.predict(k_scaled)[0]
                bb_stats = dict(
                    Oswing = stat_acc['oswings']/stat_acc['opitches'],
                    Ocontact =  stat_acc['ocontacts']/stat_acc['oswings'],
                    Zcontact =  stat_acc['zcontacts']/stat_acc['zswings'],
                    Fstrike = stat_acc['firststrikes']/stat_acc['plateappearances'],
                    SwStr = stat_acc['whiffs']/stat_acc['pitches'],
                    p_pa = stat_acc['pitches']/stat_acc['plateappearances'],
                    LkStr = stat_acc['strikeslooking']/stat_acc['pitches'],
                    FlStr = stat_acc['fouls']/stat_acc['zpitches'],
                )
                bb_scaled = bb_scaler.transform(pd.DataFrame([bb_stats])[['Oswing', 'Ocontact', 'Zcontact', 'Fstrike', 'SwStr', 'p_pa', 'LkStr', 'FlStr']])
                bb_pred = bb_lm.predict(bb_scaled)[0]
                if pa < 60:
                    k = ((steamer_projection['krate'] * (60 - pa)) + (k_pred * pa / 2) + (stat_acc['strikeouts']/pa * pa/ 2)) / 60
                    # print(k, steamer_projection['krate'], k_pred, stat_acc['strikeouts'] / pa)
                else:
                    k = k_pred

                if pa < 120:
                    bb = ((steamer_projection['bbrate'] * (120 - pa)) + (bb_pred * pa / 2) + (stat_acc['walks']/pa * pa/ 2)) / 120
                    # print(bb, steamer_projection['bbrate'], bb_pred, stat_acc['walks'] / pa)
                else:
                    bb = bb_pred

            # print(bb)
            bip = stat_acc['xwOBA_denom']
            if bip < 70:
                wobacon = (steamer_projection['wobacon'] * (70 - bip) + stat_acc['xwOBA']) / 70
            else:
                wobacon = stat_acc['xwOBA'] / bip

            # print(pa, wobacon, k, bb, hbp)
            # print(((bb * pa * 0.69) + (hbp * pa * 0.72) + \
            #         (wobacon * ((pa - (pa * (k + bb + hbp)))))) / pa)
            # print(log['game_date'].iloc[0])
            if pa == 0:
                pa = 1
            return ((bb * pa * 0.69) + (hbp * pa * 0.72) + \
                    (wobacon * (pa - (pa * (k + bb + hbp))))) / pa

        date = 0
        logs = logs.sort_values(['key', 'at_bat_number']).groupby(['key', 'at_bat_number'])
        decay_coeff = 0.999
        for ix, log in logs:
            # print(log)
            new_date = datetime.strptime(log['game_date'].iloc[0], '%m/%d/%y').strftime('%Y-%m-%d')
            if new_date != date:
                # new game
                if date == 0:
                    decay = 0
                else:
                    decay = (datetime.strptime(new_date, '%Y-%m-%d') - datetime.strptime(date, '%Y-%m-%d')).days

                date = new_date
                daily_projections.append(dict(
                    date = new_date,
                    mlb_id = log['batter'].iloc[0],
                    key = log['key'].iloc[0],
                    woba = calc_proj_woba(),
                ))

                for key in stat_acc:
                    stat_acc[key] *= (decay_coeff ** decay)

            log_sorted = log.sort_values('pitch_number')
            for ix, row in log_sorted.iterrows():
                stat_acc = analyze_pitch(row, stat_acc)

        try:
            print(
            "O-swing:", stat_acc['oswings']/stat_acc['opitches'],
            "Z-swing:", stat_acc['zswings']/stat_acc['zpitches'],
            "swing:", stat_acc['swings']/stat_acc['pitches'],"\n",
            "O-contact:", stat_acc['ocontacts']/stat_acc['oswings'],
            "Z-contact:", stat_acc['zcontacts']/stat_acc['zswings'],
            "contact:", stat_acc['contacts']/stat_acc['swings'],"\n",
            "zone:", stat_acc['zpitches']/stat_acc['pitches'],
            "F-strike:", stat_acc['firststrikes']/stat_acc['plateappearances'],
            "SwStr:", stat_acc['whiffs']/stat_acc['pitches'],"\n",
            "FlStr", stat_acc['fouls']/stat_acc['zpitches'],
            "LkStr", stat_acc['strikeslooking']/stat_acc['pitches'],
            "Barrel:", stat_acc['barrels']/stat_acc['ballsinplay'],"\n"
            "wOBA:", stat_acc['wOBA']/stat_acc['wOBA_denom'],
            "xwOBAcon:", stat_acc['xwOBA']/stat_acc['xwOBA_denom'],"\n",
            "K/PA:", stat_acc['strikeouts']/stat_acc['plateappearances'],
            "BB/PA:", stat_acc['walks']/stat_acc['plateappearances'],
        )
        except:
            print("Not enough stats for batter")
            continue
    print(pd.DataFrame(daily_projections))
    return pd.DataFrame(daily_projections)

def generate_pitcher_stats(pitchers):
    k_scaler, k_lm = pitcher_expected_stats.get_xk_regression(year)
    bb_scaler, bb_lm = pitcher_expected_stats.get_xbb_regression(year)
    daily_projections = []
    siera_total = 0
    pa_total = 0
    for ix, mlb_id in enumerate(pitchers):
        print(mlb_id, str(ix) + '/' + str(len(pitchers)))
        logs = statcast_logs[(statcast_logs['pitcher'] == mlb_id)]
        if logs.empty:
            print("Empty logs for", mlb_id)
            continue
        logs = logs.sort_values(by='game_date')
        steamer = steamer_pitchers[
            (steamer_pitchers['mlbamid'] == mlb_id) &
            (steamer_pitchers['pn'] == 1) &
            (steamer_pitchers['split'] == 'total')
        ]
        # print(steamer)
        if steamer.empty:
            print("No steamer for", mlb_id)
            continue

        steamer2 = steamer_pitchers2[steamer_pitchers2['mlbamid'] == mlb_id].iloc[0]

        stat_acc = get_stat_acc()
        stat_acc['paSP'] = steamer2['start_IP'] / steamer2['IP']

        so = steamer['SO'].sum()
        bb = steamer['BB'].sum()
        hbp = steamer['HBP'].sum()
        hr = steamer['HR'].sum()
        tbf = steamer['TBF'].sum()
        gb = steamer2['GB']
        def get_projected_wobacon(steamer):
            wobacon_numer = .89 * steamer['1b'].sum() + 1.27 * steamer['2b'].sum() + 1.62 * steamer['3B'].sum() + 2.10 * steamer['HR'].sum()
            wobacon_denom = tbf - bb - so - hbp
            return wobacon_numer / wobacon_denom

        steamer_projection = dict(
            krate = so / tbf,
            bbrate = bb / tbf,
            hbprate = hbp / tbf,
            hrrate = hr / tbf,
            gbrate = steamer2['GBrate'],
            fbrate = steamer2['FBrate'],
            wobacon = get_projected_wobacon(steamer)
        )

        def calc_proj_woba_siera():
            pa = stat_acc['plateappearances']

            if pa < 40:
                k = (steamer_projection['krate'] * (100 - pa) + stat_acc['strikeouts']) / 100
                bb = (steamer_projection['bbrate'] * (200 - pa) + stat_acc['walks']) / 200
            else:
                k_stats = dict(
                    Oswing = stat_acc['oswings']/stat_acc['opitches'],
                    contact =  stat_acc['contacts']/stat_acc['swings'],
                    SwStr = stat_acc['whiffs']/stat_acc['pitches'],
                    Fstrike = stat_acc['firststrikes']/stat_acc['plateappearances'],
                    FlStr = stat_acc['fouls']/stat_acc['zpitches'],
                    LkStr = stat_acc['strikeslooking']/stat_acc['pitches'],
                    p_pa = stat_acc['pitches']/stat_acc['plateappearances'],
                )
                k_scaled = k_scaler.transform(pd.DataFrame([k_stats])[['Oswing', 'contact', 'SwStr', 'Fstrike', 'FlStr', 'LkStr', 'p_pa']])
                k_pred = k_lm.predict(k_scaled)[0]
                bb_stats = dict(
                    swing = stat_acc['swings']/stat_acc['pitches'],
                    contact =  stat_acc['contacts']/stat_acc['swings'],
                    zone = stat_acc['zpitches']/stat_acc['pitches'],
                    Fstrike = stat_acc['firststrikes']/stat_acc['plateappearances'],
                    p_pa = stat_acc['pitches']/stat_acc['plateappearances'],
                    LkStr = stat_acc['strikeslooking']/stat_acc['pitches'],
                    FlStr = stat_acc['fouls']/stat_acc['zpitches'],
                )
                bb_scaled = bb_scaler.transform(pd.DataFrame([bb_stats])[['swing', 'contact', 'zone', 'Fstrike', 'p_pa', 'LkStr', 'FlStr']])
                bb_pred = bb_lm.predict(bb_scaled)[0]

                if pa < 100:
                    k = ((steamer_projection['krate'] * (100 - pa)) + (k_pred * pa / 2) + (stat_acc['strikeouts']/pa * pa/ 2)) / 100
                else:
                    k = k_pred

                if pa < 200:
                    bb = ((steamer_projection['bbrate'] * (200 - pa)) + (bb_pred * pa / 2) + (stat_acc['walks']/pa * pa/ 2)) / 200
                else:
                    bb = bb_pred

            if pa < 200:
                gb = (steamer_projection['gbrate'] * (200 - pa) + stat_acc['groundballs']) / 200
                fb = (steamer_projection['fbrate'] * (200 - pa) + stat_acc['flyballs']  + stat_acc['popups']) / 200
            else:
                gb = stat_acc['groundballs'] / pa
                fb = (stat_acc['flyballs'] + stat_acc['popups']) / pa

            if pa < 800:
                hbp = (steamer_projection['hbprate'] * (800 - pa) + stat_acc['hbp']) / 800
            else:
                hbp = stat_acc['hbp'] / pa

            bip = stat_acc['xwOBA_denom']
            if bip < 500:
                wobacon = (steamer_projection['wobacon'] * (500 - bip) + stat_acc['xwOBA']) / 500
            else:
                wobacon = stat_acc['xwOBA'] / bip

            # print(log['game_date'].iloc[0])
            # print(pa, wobacon, k, bb, hbp)
            # print(((bb * pa * 0.69) + (hbp * pa * 0.72) + \
            #         (wobacon * (pa - (pa * (k + bb + hbp))))) / pa)
            if pa == 0:
                pa = 1
            woba = ((bb * pa * 0.69) + (hbp * pa * 0.72) + \
                    (wobacon * (pa - (pa * (k + bb + hbp))))) / pa

            plus_minus = 2.232 * ((gb - fb) ** 2)
            plus_minus = plus_minus * -1 if gb > fb else plus_minus
            # print(k, bb, gb, fb)
            siera = 5.952 - 15.219 * k \
                    + 12.746 * (k ** 2) \
                    - 0.385 * bb \
                    + 10.671 * (bb ** 2) \
                    - 2.844 * (gb - fb) \
                    + 15.421 * k * bb \
                    + 5.226 * k * (gb - fb) \
                    + 10.150 * bb * (gb - fb) \
                    + 0.246 * (stat_acc['paSP']) + plus_minus
            # print(woba, siera)
            return woba, siera

        date = 0
        decay_coeff = 0.999
        logs = logs.sort_values(['key', 'at_bat_number']).groupby(['key', 'at_bat_number'])
        woba, siera = calc_proj_woba_siera()
        daily_projections.append(dict(
            date = '2018-03-29',
            mlb_id = mlb_id,
            key = '',
            woba = woba,
            siera = siera,
        ))
        for ix, log in logs:
            log_sorted = log.sort_values('pitch_number')
            # print(log)
            new_date = datetime.strptime(log['game_date'].iloc[0], '%m/%d/%y').strftime('%Y-%m-%d')
            if new_date != date:
                # new game
                if date == 0:
                    decay = 0
                else:
                    decay = (datetime.strptime(new_date, '%Y-%m-%d') - datetime.strptime(date, '%Y-%m-%d')).days

                date = new_date
                woba, siera = calc_proj_woba_siera()
                daily_projections.append(dict(
                    date = date,
                    mlb_id = log['pitcher'].iloc[0],
                    key = log['key'].iloc[0],
                    woba = woba,
                    siera = siera
                ))
                for key in stat_acc:
                    stat_acc[key] *= (decay_coeff ** decay)
                # print(log)

            for ix, row in log_sorted.iterrows():
                stat_acc = analyze_pitch(row, stat_acc)

        try:
            print(
            "O-swing:", stat_acc['oswings']/stat_acc['opitches'],
            "Z-swing:", stat_acc['zswings']/stat_acc['zpitches'],
            "swing:", stat_acc['swings']/stat_acc['pitches'],"\n",
            "O-contact:", stat_acc['ocontacts']/stat_acc['oswings'],
            "Z-contact:", stat_acc['zcontacts']/stat_acc['zswings'],
            "contact:", stat_acc['contacts']/stat_acc['swings'],"\n",
            "zone:", stat_acc['zpitches']/stat_acc['pitches'],
            "F-strike:", stat_acc['firststrikes']/stat_acc['plateappearances'],
            "SwStr:", stat_acc['whiffs']/stat_acc['pitches'],"\n",
            "FlStr", stat_acc['fouls']/stat_acc['zpitches'],
            "LkStr", stat_acc['strikeslooking']/stat_acc['pitches'],
            "Barrel:", stat_acc['barrels']/stat_acc['ballsinplay'],"\n"
            "wOBA:", stat_acc['wOBA']/stat_acc['wOBA_denom'],
            "xwOBAcon:", stat_acc['xwOBA']/stat_acc['xwOBA_denom'],"\n",
            "K/PA:", stat_acc['strikeouts']/stat_acc['plateappearances'],
            "BB/PA:", stat_acc['walks']/stat_acc['plateappearances'],
            'wOBA', woba, 'SIERA', siera
        )
        except:
            print("Not enough stats for batter")
            continue
        siera_total = siera_total + stat_acc['plateappearances'] * siera
        pa_total = pa_total + stat_acc['plateappearances']

    print(siera_total/pa_total)
    print(pd.DataFrame(daily_projections))
    return pd.DataFrame(daily_projections)

if __name__ == '__main__':
    # all_batters = list(set(statcast_logs['batter'].tolist()))
    # # all_batters = [664023]
    # batter_stats = generate_batter_stats(all_batters)
    # batter_stats.to_csv(os.path.join('data',
    #                                  'projections',
    #                                  'batter_statcast_proj_{}.csv'.format(year)),
    #                     index=False)
    all_pitchers = list(set(statcast_logs['pitcher'].tolist()))
    # all_pitchers = [453385]
    pitcher_stats = generate_pitcher_stats(all_pitchers)
    pitcher_stats.to_csv(os.path.join('data','projections',
                                      'pitcher_statcast_proj_{}.csv'.format(year)),
                         index=False)
