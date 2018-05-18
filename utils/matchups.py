

def generate_matchups(park_factors, home_pitchers, away_pitchers, home_batters, away_batters, league_avgs):
    matchups = dict()
    for batter in away_batters:
        for pitcher in home_pitchers:
            outcome_dict = get_outcome_distribution(park_factors, league_avgs, batter, pitcher[0])
            matchups[(pitcher[0]['mlbamid'],batter['vL']['mlbamid'])] = outcome_dict
    for batter in home_batters:
        for pitcher in away_pitchers:
            outcome_dict = get_outcome_distribution(park_factors, league_avgs, batter, pitcher[0])
            matchups[(pitcher[0]['mlbamid'],batter['vL']['mlbamid'])] = outcome_dict
    return matchups

def get_outcome_distribution(park_factors, league_avgs, batter, pitcher):
    park_factors = park_factors[0]
    pitcher_hand = pitcher['Throws']
    try:
        if pitcher_hand == 'B':
            batter_split = batter['vR'] if batter['vR']['bats'] == 'R' else batter['vL']
        else:
            batter_split = batter['v'+pitcher_hand]
    except:
        print(pitcher)
        print(batter)
    batter_hand = batter_split['bats']
    batter_hand = batter_hand if batter_hand != 'B' else ('R' if pitcher_hand == 'L' else 'L')
    outcomes_w_factor = ["1B","2B","3B","HR"]
    outcomes_wo_factor = ["K","HBP","BB"]
    outcomes = outcomes_w_factor +outcomes_wo_factor
    bat_outcomes_w_factor = {outcome: batter_split[outcome]*(park_factors[outcome+batter_hand]/100)/batter_split["PA"] for outcome in outcomes_w_factor}
    bat_outcomes_wo_factor = {outcome: batter_split[outcome]/batter_split["PA"] for outcome in outcomes_wo_factor}
    bat_outcomes = {**bat_outcomes_w_factor,**bat_outcomes_wo_factor}
    bat_outcomes["OutNonK"] = 1-sum(bat_outcomes.values())
    p_outcomes = ["K","BB","HBP","1b","2b","3b","HR"]
    pitch_outcomes = {outcome: pitcher[outcome]/pitcher["TBF"] for outcome in p_outcomes}
    pitch_outcomes["1B"] = pitch_outcomes.pop("1b")
    pitch_outcomes["2B"] = pitch_outcomes.pop("2b")
    pitch_outcomes["3B"] = pitch_outcomes.pop("3b")
    pitch_outcomes["OutNonK"] = 1-sum(pitch_outcomes.values())
    league_outcomes = dict(league_avgs)
    league_outcomes["OutNonK"] = 1-sum(league_outcomes.values())
    outcomes.append("OutNonK")
    denom = {outcome: bat_outcomes[outcome]*pitch_outcomes[outcome]/league_outcomes[outcome]
             for outcome in outcomes}
    normalizer = sum(denom.values())
    outcome_dict = {k: v/normalizer for k, v in denom.items()}
    return outcome_dict
