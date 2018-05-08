

def winpct_to_ml(winpct):
    if winpct >= .5:
        return (-100.0 * winpct)/(1-winpct)
    else:
        return (100.0 - 100.0 * winpct) / winpct

def ml_to_winpct(ml):
    if ml < 0:
        return ml/(ml-100)
    else:
        return 100/(ml+100)

def over_total_pct(histo, line):
    line = float(line)
    start = int(line + 1.0) if (line % 1.0 == 0) else int(line+0.5)
    total = 0
    for i in range(start, len(histo)):
        total += histo[i]
    return total/(10000.0-(histo[int(line)] if (line % 1.0 == 0) else 0))

# decimal to american
def d_to_a(odds):
    if odds >= 2.00:
        return (odds - 1) * 100.0
    else:
        return -100.0 / (odds - 1)

def third_kelly_calculator(odds, exp_win_pct):
    br_pct = (exp_win_pct*odds - 1)/(odds-1)*100.0/3
    return br_pct
