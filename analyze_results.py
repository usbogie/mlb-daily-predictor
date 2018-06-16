import pandas as pd
import matplotlib.pyplot as plt
import json
from itertools import groupby
import numpy as np

def bet_against_pitcher(results):
    sorted_by_bet_on = sorted(results, key = lambda i: i['bet_against_pitcher'])
    grouped = groupby(sorted_by_bet_on, lambda content: content['bet_against_pitcher'])
    pitchers = []
    for pitcher, outcomes in grouped:
        y = sum([x['net'] for x in outcomes])
        pitchers.append([pitcher, y])
    sorted_pitchers = (sorted(pitchers, key = lambda i: i[1]))
    print(sorted_pitchers)
    teams = []
    amounts = []
    for team, amount in sorted_pitchers:
        if amount > -20:
            continue
        teams.append(team)
        amounts.append(amount)

    index = np.arange(len(teams))
    plt.bar(index, amounts)
    plt.xticks(index, tuple(teams), rotation = 'vertical')
    plt.ylabel('Net')
    plt.title('Amount bet on each team')
    plt.show()

def value_strati(results):
    values = [[2,5],[5,8],[8,11],[11,13],[13,25],]
    ticks = []
    amounts = []
    for value in values:
        ticks.append('{}-{}'.format(value[0],value[1]))
        total_risk = sum([x['k_risk'] for x in results if x['value'] >= value[0] and x['value'] < value[1]])
        total_net = sum([x['net'] for x in results if x['value'] >= value[0] and x['value'] < value[1]])
        amounts.append(total_net/total_risk*100.0)
    index = np.arange(len(ticks))
    plt.bar(index, amounts)
    plt.xticks(index, tuple(ticks), rotation = 'vertical')
    plt.ylabel('Net')
    plt.title('Values')
    plt.show()

with open ('data/results/results_2018.json', 'r') as f:
    results = json.load(f)

value_strati(results)
