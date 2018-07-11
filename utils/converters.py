def amount_won(risk, odds):
    return int(risk * (odds-1))

def winpct_to_ml(winpct):
    if winpct >= .5:
        return int((-100 * winpct) / (1 - winpct))
    else:
        return int((100 - 100 * winpct) / winpct)

def ml_to_winpct(ml):
    return (100 / ml)

def over_total_pct(histo, line):
    line = float(line)
    start = int(line + 1.0) if (line % 1.0 == 0) else int(line+0.5)
    total = 0
    for i in range(start, len(histo)):
        total += histo[i]
    return total/(10000-(histo[int(line)] if (line % 1.0 == 0) else 0))

# decimal to american
def d_to_a(odds):
    if odds >= 2:
        return int((odds - 1) * 100)
    else:
        return int(-100 / (odds - 1))

def third_kelly_calculator(odds, exp_win_pct):
    br_pct = (exp_win_pct * odds - 1) / (odds - 1) * 100 / 3
    return br_pct
