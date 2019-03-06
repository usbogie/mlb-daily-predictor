import pandas as pd
import numpy as np
import os
import copy


year = 2018
statcast_logs = pd.read_csv(os.path.join('data','statcast','{}.csv'.format(year)))
steamer_pitchers = pd.read_csv(os.path.join('data','steamer', 'steamer_pitchers_{}.csv'.format(year)))
steamer_batters_split = pd.read_csv(os.path.join('data','steamer', 'steamer_hitters_{}_split.csv'.format(year)))

pd.set_option('display.max_rows', 500)

def generate_batter_stats(batters):
    players = []
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
            # continue
        else:
            steamer = steamer.iloc[0]

        stat_acc = dict(
            whiffs = 0,
            opitches = 0,
            zpitches = 0,
            pitches = 0,
            oswings = 0,
            zswings = 0,
            swings = 0,
            ocontacts = 0,
            zcontacts = 0,
            contacts = 0,
            firststrikes = 0,
            plateappearances = 0,

            xwOBA = 0,
            xwOBA_denom = 0,
            wOBA = 0,
            wOBA_denom = 0,

            ballsinplay = 0,
            barrels = 0,
            flyballs = 0,
            popups = 0,
            groundballs = 0,
            linedrives = 0,

            strikeouts = 0,
            walks = 0,
        )

        def is_strike(row):
            # return row['zone'] in range(1,10)
            return (row['plate_x'] <= 0.83 and row['plate_x'] >= -0.83 \
                and row['plate_z'] <= row['sz_top'] + 0.02\
                and row['plate_z'] >= row['sz_bot'] - 0.02)

        logs = logs.sort_values(['key', 'at_bat_number']).groupby(['key', 'at_bat_number'])

        stat_60_freeze = None
        for ix, log in logs:
            log_sorted = log.sort_values('pitch_number')
            # print(log_sorted)
            # print(type(log_sorted))
            for ix, row in log_sorted.iterrows():
                if row['pitch_number'] == 1 and ('strike' in row['description'] \
                        or 'foul' in row['description'] or 'hit' in row['description'] \
                        or row['description'] == 'missed_bunt' or row['description'] == 'swinging_pitchout'):
                    stat_acc['firststrikes'] = stat_acc['firststrikes'] + 1

                if row['description'] == 'called_strike' or row['description'] == 'pitchout' \
                        or row['description'] == 'hit_by_pitch' or row['description'] == 'ball' \
                        or row['description'] == 'blocked_ball':
                    stat_acc['pitches'] = stat_acc['pitches'] + 1
                    if is_strike(row):
                        stat_acc['zpitches'] = stat_acc['zpitches'] + 1
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

                # if stat_acc['plateappearances'] >= 60 and stat_60_freeze is None:
                #     stat_60_freeze = copy.deepcopy(stat_acc)

        try:
            players.append(dict(
                Oswing = stat_acc['oswings']/stat_acc['opitches'],
                Zswing = stat_acc['zswings']/stat_acc['zpitches'],
                swing = stat_acc['swings']/stat_acc['pitches'],
                Ocontact = stat_acc['ocontacts']/stat_acc['oswings'],
                Zcontact = stat_acc['zcontacts']/stat_acc['zswings'],
                contact = stat_acc['contacts']/stat_acc['swings'],
                zone = stat_acc['zpitches']/stat_acc['pitches'],
                Fstrike = stat_acc['firststrikes']/stat_acc['plateappearances'],
                SwStr = stat_acc['whiffs']/stat_acc['pitches'],
                Barrel = stat_acc['barrels']/stat_acc['ballsinplay'],
                wOBACON = stat_acc['wOBA']/stat_acc['wOBA_denom'],
                xwOBACON = stat_acc['xwOBA']/stat_acc['wOBA_denom'],
                k_pa = stat_acc['strikeouts']/stat_acc['plateappearances'],
                bb_pa = stat_acc['walks']/stat_acc['plateappearances'],
                p_pa = stat_acc['pitches']/stat_acc['plateappearances'],
                pa = stat_acc['plateappearances'],
                mlb_id = mlb_id,
            ))
        except:
            print("Not enough stats for batter")
            continue

        print(stat_acc)
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
            "Barrel%:", stat_acc['barrels']/stat_acc['ballsinplay'],
            "wOBA:", stat_acc['wOBA']/stat_acc['wOBA_denom'],
            "xwOBAcon%:", stat_acc['xwOBA']/stat_acc['xwOBA_denom'],"\n",
            "K/PA:", stat_acc['strikeouts']/stat_acc['plateappearances'],
            "BB/PA%:", stat_acc['walks']/stat_acc['plateappearances'],
        )

    return pd.DataFrame(players)


def generate_pitcher_stats(pitchers):
    players = []
    for ix, mlb_id in enumerate(pitchers):
        print(mlb_id, str(ix) + '/' + str(len(pitchers)))
        logs = statcast_logs[statcast_logs['pitcher'] == mlb_id]
        if logs.empty:
            print("Empty logs for", mlb_id)
            continue
        logs = logs.sort_values(by='game_date')
        print((logs[pd.isnull(logs['pitch_type'])]))
        steamer = steamer_pitchers[steamer_pitchers['mlbamid'] == mlb_id]
        if steamer.empty:
            print("No steamer for", mlb_id)
            # continue
        else:
            steamer = steamer.iloc[0]

        stat_acc = dict(
            whiffs = 0,
            opitches = 0,
            zpitches = 0,
            pitches = 0,
            oswings = 0,
            zswings = 0,
            swings = 0,
            ocontacts = 0,
            zcontacts = 0,
            contacts = 0,
            firststrikes = 0,
            battersfaced = 0,

            xwOBA = 0,
            xwOBA_denom = 0,
            wOBA = 0,
            wOBA_denom = 0,

            ballsinplay = 0,
            barrels = 0,
            flyballs = 0,
            popups = 0,
            groundballs = 0,
            linedrives = 0,

            strikeouts = 0,
            walks = 0,
        )

        def is_strike(row):
            return row['zone'] in range(1,10)
            # return (row['plate_x'] <= 0.83 and row['plate_x'] >= -0.83 \
            #     and row['plate_z'] <= row['sz_top'] + 0.02\
            #     and row['plate_z'] >= row['sz_bot'] - 0.02)

        logs = logs.sort_values(['key', 'at_bat_number']).groupby(['key', 'at_bat_number'])

        stat_60_freeze = None
        for ix, log in logs:
            log_sorted = log.sort_values('pitch_number')
            # print(log_sorted)
            # print(type(log_sorted))
            for ix, row in log_sorted.iterrows():
                if row['pitch_number'] == 1 and ('strike' in row['description'] \
                        or 'foul' in row['description'] or 'hit' in row['description'] \
                        or row['description'] == 'missed_bunt' or row['description'] == 'swinging_pitchout'):
                    stat_acc['firststrikes'] = stat_acc['firststrikes'] + 1

                if row['description'] == 'called_strike' or row['description'] == 'pitchout' \
                        or row['description'] == 'hit_by_pitch' or row['description'] == 'ball' \
                        or row['description'] == 'blocked_ball':
                    stat_acc['pitches'] = stat_acc['pitches'] + 1
                    if is_strike(row):
                        stat_acc['zpitches'] = stat_acc['zpitches'] + 1
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
                        or row['events'] == 'sac_bunt_double_play' or row['events'] == 'sac_bunt' \
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
                    stat_acc['battersfaced'] = stat_acc['battersfaced'] + 1
                elif row['events'] == 'hit_by_pitch' or row['events'] == 'strikeout' \
                        or row['events'] == 'strikeout_double_play' or row['events'] == 'walk':
                    # stat_acc['xwOBA'] = stat_acc['xwOBA'] + row['woba_value']
                    stat_acc['wOBA'] = stat_acc['wOBA'] + row['woba_value']
                    stat_acc['wOBA_denom'] = stat_acc['wOBA_denom'] + row['woba_denom']
                    stat_acc['battersfaced'] = stat_acc['battersfaced'] + 1
                    if row['events'] == 'strikeout' \
                            or row['events'] == 'strikeout_double_play':
                        stat_acc['strikeouts'] = stat_acc['strikeouts'] + 1
                    elif row['events'] == 'walk':
                        stat_acc['walks'] = stat_acc['walks'] + 1

                # if stat_acc['plateappearances'] >= 60 and stat_60_freeze is None:
                #     stat_60_freeze = copy.deepcopy(stat_acc)

        try:
            players.append(dict(
                Oswing = stat_acc['oswings']/stat_acc['opitches'],
                Zswing = stat_acc['zswings']/stat_acc['zpitches'],
                swing = stat_acc['swings']/stat_acc['pitches'],
                Ocontact = stat_acc['ocontacts']/stat_acc['oswings'],
                Zcontact = stat_acc['zcontacts']/stat_acc['zswings'],
                contact = stat_acc['contacts']/stat_acc['swings'],
                zone = stat_acc['zpitches']/stat_acc['pitches'],
                Fstrike = stat_acc['firststrikes']/stat_acc['battersfaced'],
                SwStr = stat_acc['whiffs']/stat_acc['pitches'],
                Barrel = stat_acc['barrels']/stat_acc['ballsinplay'],
                wOBACON = stat_acc['wOBA']/stat_acc['wOBA_denom'],
                xwOBACON = stat_acc['xwOBA']/stat_acc['wOBA_denom'],
                k_pa = stat_acc['strikeouts']/stat_acc['battersfaced'],
                bb_pa = stat_acc['walks']/stat_acc['battersfaced'],
                p_pa = stat_acc['pitches']/stat_acc['battersfaced'],
                bf = stat_acc['battersfaced'],
                mlb_id = mlb_id
            ))
        except:
            print("Not enough stats for pitcher")
            continue

        print(stat_acc)
        print(
            "O-swing:", stat_acc['oswings']/stat_acc['opitches'],
            "Z-swing:", stat_acc['zswings']/stat_acc['zpitches'],
            "swing:", stat_acc['swings']/stat_acc['pitches'],"\n",
            "O-contact:", stat_acc['ocontacts']/stat_acc['oswings'],
            "Z-contact:", stat_acc['zcontacts']/stat_acc['zswings'],
            "contact:", stat_acc['contacts']/stat_acc['swings'],"\n",
            "zone:", stat_acc['zpitches']/stat_acc['pitches'],
            "F-strike:", stat_acc['firststrikes']/stat_acc['battersfaced'],
            "SwStr:", stat_acc['whiffs']/stat_acc['pitches'],"\n",
            "Barrel%:", stat_acc['barrels']/stat_acc['ballsinplay'],
            "wOBA:", stat_acc['wOBA']/stat_acc['wOBA_denom'],
            "xwOBAcon%:", stat_acc['xwOBA']/stat_acc['xwOBA_denom'],"\n",
            "K/PA:", stat_acc['strikeouts']/stat_acc['battersfaced'],
            "BB/PA%:", stat_acc['walks']/stat_acc['battersfaced'],
        )

    return pd.DataFrame(players)


if __name__ == '__main__':
    # all_batters = list(set(statcast_logs['batter'].tolist()))
    # print(all_batters)
    # all_batters = [571740]
    # batter_stats = generate_batter_stats(all_batters)
    # batter_stats.to_csv(os.path.join('data',
    #                                  'projections',
    #                                  'batter_statcast_{}.csv'.format(year)),
    #                     index=False)
    # print()
    # all_pitchers = list(set(statcast_logs['pitcher'].tolist()))
    all_pitchers = [605483]
    pitcher_stats = generate_pitcher_stats(all_pitchers)
    # pitcher_stats.to_csv(os.path.join('data','projections',
    #                                   'pitcher_statcast_{}.csv'.format(year)),
    #                      index=False)
    # create_team_stats()
