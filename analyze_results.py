import pandas as pd
import matplotlib.pyplot as plt
import json
from itertools import groupby
import numpy as np

def bet_against_pitcher(results):
    type = 'bet_on_pitcher'
    sorted_by_bet_on = sorted(results, key = lambda i: i[type])
    grouped = groupby(sorted_by_bet_on, lambda content: content[type])
    pitchers = []
    for pitcher, outcomes in grouped:
        outcome_list = list(outcomes)
        y = sum([x['net'] for x in outcome_list])
        pitchers.append([pitcher, y])
        # denom = sum([x['k_risk'] for x in outcome_list])
        # pitchers.append([pitcher, y/denom if denom != 0 else 0])
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

def line_ranges_results(results):
    ranges = [[1000, 300],[300,250],[250,200],[200,150],[150,125],[125,100],[-99,-125],[-125,-150],
              [-150,-175],[-175,-200],[-200,-250],[-250,-300],[-300,-1000]]
    ticks = []
    amounts = []
    for range in ranges:
        ticks.append('{}-{}'.format(range[0],range[1]))
        print('{}-{}'.format(range[0],range[1]),
                len([x for x in results if x['net'] > 0 and x['line'] < range[0] and x['line'] >= range[1]]),'-',
                len([x for x in results if x['net'] < 0 and x['line'] < range[0] and x['line'] >= range[1]]))
        total_risk = sum([x['k_risk'] for x in results if x['line'] < range[0] and x['line'] >= range[1]])
        total_net = sum([x['net'] for x in results if x['line'] < range[0] and x['line'] >= range[1]])
        amount = 0 if total_risk == 0 else total_net
        amounts.append(amount)
    index = np.arange(len(ticks))
    plt.bar(index, amounts)
    plt.xticks(index, tuple(ticks), rotation = 'vertical')
    plt.ylabel('Net')
    plt.title('Values')
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
