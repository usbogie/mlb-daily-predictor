import pandas as pd
import matplotlib.pyplot as plt
import json
from itertools import groupby
import numpy as np

def bet_against_pitcher(results):
    sorted_by_bet_against = sorted(results, key = lambda i: i['bet_against'])
    grouped = groupby(sorted_by_bet_against, lambda content: content['bet_against'])
    pitchers = []
    for pitcher, outcomes in grouped:
        y = sum([x['k_risk'] for x in outcomes])
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
    values = [[0,1],[1,2],[2,3],[3,4],[4,5],[5,6],[6,7],[7,8],[8,9],[9,10],[10,11],[11,12],[12,13],[13,20]]
    ticks = []
    amounts = []
    for value in values:
        ticks.append('{}-{}'.format(value[0],value[1]))
        print('{}-{}'.format(value[0],value[1]),
                len([x for x in results if x['side_value'] >= value[0] and x['side_value'] < value[1] and x['net'] > 0]),'-',
                len([x for x in results if x['side_value'] >= value[0] and x['side_value'] < value[1] and x['net'] < 0]))
        total_risk = sum([x['k_risk'] for x in results if x['side_value'] >= value[0]])
        total_net = sum([x['net'] for x in results if x['side_value'] >= value[0]])
        amount = 0 if total_risk == 0 else total_net/total_risk*100
        amounts.append(amount)
    index = np.arange(len(ticks))
    plt.bar(index, amounts)
    plt.xticks(index, tuple(ticks), rotation = 'vertical')
    plt.ylabel('Net')
    plt.title('Values')
    plt.show()

def value_total_strati(results):
    values = [[5,6],[6,7],[7,8],[8,9],[9,10],[10,11],[11,12],[12,13],[13,14],[14,15],[16,17],[17,18],[18,40]]
    ticks = []
    amounts = []
    for value in values:
        ticks.append('{}-{}'.format(value[0],value[1]))
        print('{}-{}'.format(value[0],value[1]),
                len([x for x in results if x['t_value'] >= value[0] and x['t_value'] < value[1] and x['t_net'] > 0]),'-',
                len([x for x in results if x['t_value'] >= value[0] and x['t_value'] < value[1] and x['t_net'] < 0]))
        total_risk = sum([x['t_risk'] for x in results if x['t_value'] >= value[0]])
        total_net = sum([x['t_net'] for x in results if x['t_value'] >= value[0]])
        amount = 0 if total_risk == 0 else total_net/total_risk*100
        amounts.append(amount)
    index = np.arange(len(ticks))
    plt.bar(index, amounts)
    plt.xticks(index, tuple(ticks), rotation = 'vertical')
    plt.ylabel('Net')
    plt.title('Values')
    plt.show()


with open ('data/results/results_2018.json', 'r') as f:
    results = json.load(f)

value_side_strati(results)
