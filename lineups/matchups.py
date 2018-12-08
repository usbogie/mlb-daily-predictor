import numpy as np

def get_split_avgs(split, bats, pitcher_split):
    split = split[(split['bats'].isin([bats,'B'])) & (split['split'] == pitcher_split)]
    total_PA = float(split['PA'].sum())
    avgs_dict = dict()
    avgs_dict['hit'] = (split['H'].sum() - split['HR'].sum()) / total_PA
    avgs_dict['hr'] = split['HR'].sum() / total_PA
    avgs_dict['bb'] = split['BB'].sum() / total_PA
    avgs_dict['hbp'] = split['HBP'].sum() / total_PA
    avgs_dict['k'] = split['K'].sum() / total_PA
    return avgs_dict

def calc_averages(steamer_batters):
    steamer_batters = steamer_batters[steamer_batters['pn'] == 1]
    bL_v_pL = get_split_avgs(steamer_batters, 'L', 'vL')
    bL_v_pR = get_split_avgs(steamer_batters, 'L', 'vR')
    bR_v_pL = get_split_avgs(steamer_batters, 'R', 'vL')
    bR_v_pR = get_split_avgs(steamer_batters, 'R', 'vR')
    return dict(
        bL_v_pL = bL_v_pL,
        bL_v_pR = bL_v_pR,
        bR_v_pL = bR_v_pL,
        bR_v_pR = bR_v_pR,
    )

def generate_matchups(park_factors, steamer_batters, home_pitchers, away_pitchers, home_batters, away_batters, home_defense, away_defense, league_avgs, temp):
    matchups = dict()
    for batter in away_batters:
        for pitcher in home_pitchers:
            outcome_dict = get_outcome_distribution(park_factors, league_avgs, batter, pitcher, home_defense, temp)
            matchups[(pitcher['mlb_id'],batter['mlb_id'])] = outcome_dict
    for batter in home_batters:
        for pitcher in away_pitchers:
            outcome_dict = get_outcome_distribution(park_factors, league_avgs, batter, pitcher, away_defense, temp)
            matchups[(pitcher['mlb_id'],batter['mlb_id'])] = outcome_dict

    return matchups

def get_outcome_distribution(park_factors, league_avgs, batter, pitcher, defense, temp):
    park_factors = park_factors[0]
    pitcher_hand = pitcher['vL']['throws']
    batter_hand = batter['vR']['bats']
    batter_hand = batter_hand if batter_hand != 'B' else ('R' if pitcher_hand == 'L' else 'L')
    if pitcher_hand == 'B':
        batter_split = batter['vR'] if batter['vR']['bats'] == 'R' else batter['vL']
        pitcher_hand = 'R' if batter['vR']['bats'] == 'R' else 'L'
    else:
        batter_split = batter['v'+pitcher_hand]
    pitcher_split = pitcher['v'+batter_hand]

    split_avgs = league_avgs['b{}_v_p{}'.format(batter_hand,pitcher_hand)]

    temp_hit_adj = 0.8416988 + (1.025144 - 0.8416988)/(1 + (temp/92.86499) ** 4.391434)
    temp_hr_adj = 0.3639859 + (1.571536 - 0.3639859)/(1 + (temp/67.64016) ** 1.381388)

    batter_split['hit'] = batter_split['single'] + batter_split['double'] + batter_split['triple']
    pitcher_split['hit'] = pitcher_split['single'] + pitcher_split['double'] + pitcher_split['triple']

    outcomes_w_factor_w_defense = ['hit']
    outcomes_w_factor = ['hr']
    outcomes_wo_factor = ['k','hbp','bb']
    outcomes = outcomes_w_factor + outcomes_wo_factor + outcomes_w_factor_w_defense
    bat_outcomes = {outcome: batter_split[outcome] for outcome in outcomes}
    bat_outcomes['OutNonK'] = 1-sum(bat_outcomes.values())
    pitch_outcomes = {outcome: pitcher_split[outcome] for outcome in outcomes}
    pitch_outcomes['OutNonK'] = 1-sum(pitch_outcomes.values())
    league_outcomes = dict(split_avgs)
    league_outcomes['OutNonK'] = 1-sum(league_outcomes.values())
    outcomes.append('OutNonK')
    comb_outcomes_w_factor_w_defense = {outcome: (bat_outcomes[outcome]*pitch_outcomes[outcome]/league_outcomes[outcome])*((park_factors['single'+batter_hand] + park_factors['double'+batter_hand] + park_factors['triple'+batter_hand])/3/100)/defense for outcome in outcomes_w_factor_w_defense}
    comb_outcomes_w_factor = {outcome: (bat_outcomes[outcome]*pitch_outcomes[outcome]/league_outcomes[outcome])*(park_factors[outcome+batter_hand]/100)/temp_hr_adj for outcome in outcomes_w_factor}
    comb_outcomes_wo_factor = {outcome: bat_outcomes[outcome]*pitch_outcomes[outcome]/league_outcomes[outcome] for outcome in outcomes_wo_factor}
    denom = {**comb_outcomes_w_factor,**comb_outcomes_wo_factor,**comb_outcomes_w_factor_w_defense}
    denom['OutNonK'] = 1-sum(denom.values())
    normalizer = sum(denom.values())
    outcome_dict = {k: v/normalizer for k, v in denom.items()}
    outcome_dict['triple'] = outcome_dict['hit'] * .02
    outcome_dict['double'] = outcome_dict['hit'] * .24
    outcome_dict['single'] = outcome_dict['hit'] * .74
    del outcome_dict['hit']
    acc = 0
    ret = []
    for key, val in outcome_dict.items():
        acc = acc + val
        ret.append((key, acc))
    return ret
