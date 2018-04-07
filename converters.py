

def winpct_to_moneyline(winpct):
    if winpct >= .5:
        return (-100.0 * winpct)/(1-winpct)
    else:
        return (100.0 - 100.0 * winpct) / winpct

def over_total_pct(histo, line):
    line = float(line)
    start = int(line + 1.0) if (line % 1.0 == 0) else int(line+0.5)
    total = 0
    for i in range(start, len(histo)):
        total += histo[i]
    return total/(10000.0-(histo[int(line)] if (line % 1.0 == 0) else 0))
