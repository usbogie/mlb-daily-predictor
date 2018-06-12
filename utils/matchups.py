import numpy as np

def generate_matchups(park_factors, home_pitchers, away_pitchers, home_batters, away_batters, league_avgs):
    matchups = dict()
    for batter in away_batters:
        for pitcher in home_pitchers:
            outcome_dict = get_outcome_distribution(park_factors, league_avgs, batter, pitcher)
            matchups[(pitcher['vL']['mlb_id'],batter['vL']['mlb_id'])] = outcome_dict
    for batter in home_batters:
        for pitcher in away_pitchers:
            outcome_dict = get_outcome_distribution(park_factors, league_avgs, batter, pitcher)
            matchups[(pitcher['vL']['mlb_id'],batter['vL']['mlb_id'])] = outcome_dict

    return matchups

def get_outcome_distribution(park_factors, league_avgs, batter, pitcher):
    park_factors = park_factors[0]
    pitcher_hand = pitcher['vL']['throws']
    batter_hand = batter['vR']['bats']
    batter_hand = batter_hand if batter_hand != 'B' else ('R' if pitcher_hand == 'L' else 'L')
    if pitcher_hand == 'B':
        batter_split = batter['vR'] if batter['vR']['bats'] == 'R' else batter['vL']
    else:
        batter_split = batter['v'+pitcher_hand]

    if batter_hand == 'B':
        pitcher_split = pitcher['vL'] if pitcher['vR']['throws'] == 'R' else batter['vR']
    else:
        pitcher_split = pitcher['v'+batter_hand]

    outcomes_w_factor = ["single","double","triple","hr"]
    outcomes_wo_factor = ["k","hbp","bb"]
    outcomes = outcomes_w_factor + outcomes_wo_factor
    bat_outcomes = {outcome: batter_split[outcome] for outcome in outcomes}
    bat_outcomes["OutNonK"] = 1-sum(bat_outcomes.values())
    p_outcomes = ["single","double","triple","hr","k","hbp","bb"]
    pitch_outcomes = {outcome: pitcher_split[outcome] for outcome in p_outcomes}
    pitch_outcomes["OutNonK"] = 1-sum(pitch_outcomes.values())
    league_outcomes = dict(league_avgs)
    league_outcomes["OutNonK"] = 1-sum(league_outcomes.values())
    outcomes.append("OutNonK")
    comb_outcomes_w_factor = {outcome: (bat_outcomes[outcome]*pitch_outcomes[outcome]/league_outcomes[outcome])*(park_factors[outcome+batter_hand]/100) for outcome in outcomes_w_factor}
    comb_outcomes_wo_factor = {outcome: bat_outcomes[outcome]*pitch_outcomes[outcome]/league_outcomes[outcome] for outcome in outcomes_wo_factor}
    denom = {**comb_outcomes_w_factor,**comb_outcomes_wo_factor}
    denom["OutNonK"] = 1-sum(denom.values())
    normalizer = sum(denom.values())
    outcome_dict = {k: v/normalizer for k, v in denom.items()}
    acc = 0
    ret = []
    for key, val in outcome_dict.items():
        acc = acc + val
        ret.append((key, acc))
    return ret
