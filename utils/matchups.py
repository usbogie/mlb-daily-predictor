import numpy as np

def generate_matchups(park_factors, home_pitchers, away_pitchers, home_batters, away_batters, league_avgs):
    matchups = dict()
    for batter in away_batters:
        for pitcher in home_pitchers:
            outcome_dict = get_outcome_distribution(park_factors, league_avgs, batter, pitcher)
            matchups[(pitcher['vL']['mlbamid'],batter['vL']['mlbamid'])] = outcome_dict
    for batter in home_batters:
        for pitcher in away_pitchers:
            outcome_dict = get_outcome_distribution(park_factors, league_avgs, batter, pitcher)
            matchups[(pitcher['vL']['mlbamid'],batter['vL']['mlbamid'])] = outcome_dict

    return matchups

def get_outcome_distribution(park_factors, league_avgs, batter, pitcher):
    park_factors = park_factors[0]
    pitcher_hand = pitcher['vL']['Throws']
    batter_hand = batter['vR']['bats']
    batter_hand = batter_hand if batter_hand != 'B' else ('R' if pitcher_hand == 'L' else 'L')
    try:
        if pitcher_hand == 'B':
            batter_split = batter['vR'] if batter['vR']['bats'] == 'R' else batter['vL']
        else:
            batter_split = batter['v'+pitcher_hand]

        if batter_hand == 'B':
            pitcher_split = pitcher['vL'] if pitcher['vR']['Throws'] == 'R' else batter['vR']
        else:
            pitcher_split = pitcher['v'+batter_hand]
    except:
        print(pitcher)
        print(batter)

    outcomes_w_factor = ["1B","2B","3B","HR"]
    outcomes_wo_factor = ["K","HBP","BB"]
    outcomes = outcomes_w_factor + outcomes_wo_factor
    bat_outcomes_w_factor = {outcome: batter_split[outcome]*(park_factors[outcome+batter_hand]/100)/batter_split["PA"] for outcome in outcomes_w_factor}
    bat_outcomes_wo_factor = {outcome: batter_split[outcome]/batter_split["PA"] for outcome in outcomes_wo_factor}
    bat_outcomes = {**bat_outcomes_w_factor,**bat_outcomes_wo_factor}
    bat_outcomes["OutNonK"] = 1-sum(bat_outcomes.values())
    p_outcomes = ["SO/PA","BB/PA","HBP/PA","1B/PA","2B/PA","3B/PA","HR/PA"]
    pitch_outcomes = {outcome: pitcher_split[outcome] for outcome in p_outcomes}
    pitch_outcomes["K"] = pitch_outcomes.pop("SO/PA")
    pitch_outcomes["BB"] = pitch_outcomes.pop("BB/PA")
    pitch_outcomes["HBP"] = pitch_outcomes.pop("HBP/PA")
    pitch_outcomes["1B"] = pitch_outcomes.pop("1B/PA")
    pitch_outcomes["2B"] = pitch_outcomes.pop("2B/PA")
    pitch_outcomes["3B"] = pitch_outcomes.pop("3B/PA")
    pitch_outcomes["HR"] = pitch_outcomes.pop("HR/PA")
    pitch_outcomes["OutNonK"] = 1-sum(pitch_outcomes.values())
    league_outcomes = dict(league_avgs)
    league_outcomes["OutNonK"] = 1-sum(league_outcomes.values())
    outcomes.append("OutNonK")
    denom = {outcome: bat_outcomes[outcome]*pitch_outcomes[outcome]/league_outcomes[outcome]
             for outcome in outcomes}
    normalizer = sum(denom.values())
    outcome_dict = {k: v/normalizer for k, v in denom.items()}
    return outcome_dict
