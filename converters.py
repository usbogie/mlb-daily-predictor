

def winpct_to_moneyline(winpct):
    if winpct >= .5:
        return round((-100.0 * winpct)/(1-winpct), 4)
    else:
        return round((100.0 - 100.0 * winpct) / winpct, 4)

def over_total_pct(histo, line):
    line = float(line)
    start = int(line + 1.0) if (line % 1.0 == 0) else int(line+0.5)
    total = 0
    for i in range(start, len(histo)):
        total += histo[i]
    return round(total/(10000.0-(histo[int(line)] if (line % 1.0 == 0) else 0)), 4)

# decimal to american
def d_to_a(odds):
    if odds >= 2.00:
        return round((odds - 1) * 100.0, 0)
    else:
        return round(-100.0 / (odds - 1), 0)
