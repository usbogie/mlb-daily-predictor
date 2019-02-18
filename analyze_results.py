import pandas as pd
import matplotlib.pyplot as plt
import json
from itertools import groupby
import numpy as np

def bet_against_pitcher(results):
    sorted_by_bet_on = sorted(results, key = lambda i: i['bet_on'])
    grouped = groupby(sorted_by_bet_on, lambda content: content['bet_on'])
    pitchers = []
    for pitcher, outcomes in grouped:
        y = sum([x['net'] for x in outcomes])
        pitchers.append([pitcher, y])
    sorted_pitchers = (sorted(pitchers, key = lambda i: i[1]))
    print(sorted_pitchers)
    teams = []
    amounts = []
    for team, amount in sorted_pitchers:
        teams.append(team)
        amounts.append(amount)

    index = np.arange(len(teams))
    plt.bar(index, amounts)
    plt.xticks(index, tuple(teams), rotation = 'vertical')
    plt.ylabel('Net')
    plt.title('Amount bet on each team')
    plt.show()

def value_side_strati(results):
    values = [[0,2],[2,4],[4,6],[6,8],[8,10],[10,12],[12,14],[14,16],
              [16,20],[20,28],[28,50]]
    ticks = []
    amounts = []
    for value in values:
        ticks.append('{}-{}'.format(value[0],value[1]))
        print('{}-{}'.format(value[0],value[1]),
                len([x for x in results if x['side_value'] >= value[0] and x['side_value'] < value[1] and x['net'] > 0]),'-',
                len([x for x in results if x['side_value'] >= value[0] and x['side_value'] < value[1] and x['net'] < 0]))
        total_risk = sum([x['k_risk'] for x in results if x['side_value'] >= value[0] and x['side_value'] < value[1]])
        total_net = sum([x['net'] for x in results if x['side_value'] >= value[0] and x['side_value'] < value[1]])
        amount = 0 if total_risk == 0 else total_net/total_risk* 100
        amounts.append(amount)
    index = np.arange(len(ticks))
    plt.bar(index, amounts)
    plt.xticks(index, tuple(ticks), rotation = 'vertical')
    plt.ylabel('Net')
    plt.title('Values')
    plt.show()

with open ('data/results/results_2015.json', 'r') as f:
    results = json.load(f)

value_side_strati(results)
