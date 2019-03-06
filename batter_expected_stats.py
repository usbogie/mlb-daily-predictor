import pandas as pd
import numpy as np
import os
import copy
import matplotlib.pyplot as plt
import seaborn as sns

import itertools

from pyearth import Earth

from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score
from sklearn.preprocessing import MinMaxScaler

statcast_2015 = pd.read_csv(os.path.join('data','projections','batter_statcast_2015.csv'))
statcast_2016 = pd.read_csv(os.path.join('data','projections','batter_statcast_2016.csv'))
statcast_2017 = pd.read_csv(os.path.join('data','projections','batter_statcast_2017.csv'))
statcast_2018 = pd.read_csv(os.path.join('data','projections','batter_statcast_2018.csv'))

def get_xk_regression():
    columns = [
        'Oswing','Zswing','swing','Ocontact','Zcontact','contact','zone',
        'Fstrike','SwStr','p_pa'
    ]
    label = 'k_pa'

    dataset = pd.concat([
        statcast_2018[statcast_2018['pa'] >= 70][columns + [label]],
        statcast_2017[statcast_2017['pa'] >= 70][columns + [label]],
        statcast_2016[statcast_2016['pa'] >= 70][columns + [label]],
        statcast_2015[statcast_2015['pa'] >= 70][columns + [label]],
    ])
    #
    # sns.pairplot(dataset)
    # plt.show()

    print(dataset.corr())

    # for L in range(1, len(columns)+1):
    #     for subset in itertools.combinations(columns, L):
    #         print(list(subset))
    #         X = dataset[list(subset)]
    #         y = dataset[label]
    #
    #         X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=101)
    #
    #         lm = LinearRegression()
    #         lm.fit(X_train,y_train)
    #         predictions = lm.predict(X_test)
    #         score = r2_score(y_test,predictions)
    #         print(r2_score(y_test,predictions))
    #         if score > hi_score:
    #             hi_score = score
    #             hi_set = list(subset)

    hi_set = ['Zswing', 'Ocontact', 'Fstrike', 'SwStr', 'p_pa']
    scaler = MinMaxScaler()
    scaler.fit(dataset[hi_set])
    X_train = scaler.transform(dataset[hi_set])
    X_test = scaler.transform(statcast_2018[statcast_2018['pa'] >= 120][hi_set])
    # X = dataset[hi_set]
    y_train = dataset[label]
    y_test = statcast_2018[statcast_2018['pa'] >= 120][label]
    lm = Earth(max_degree=10, feature_importance_type='gcv')
    lm.fit(X_train,y_train)
    print(lm.feature_importances_)
    print(lm.trace())
    print(lm.summary())
    predictions = lm.predict(X_test)
    plt.scatter(y_test,predictions)
    print("Best:")
    print(r2_score(y_test,predictions))

    plt.show()

def get_xbb_regression():
    columns = [
        'Oswing','Zswing','swing','Ocontact','Zcontact','contact','zone',
        'Fstrike','SwStr','p_pa'
    ]
    label = 'bb_pa'

    dataset = pd.concat([
        statcast_2017[statcast_2017['pa'] >= 120][columns + [label]],
        statcast_2016[statcast_2016['pa'] >= 120][columns + [label]],
        statcast_2015[statcast_2015['pa'] >= 120][columns + [label]],
    ])

    print(dataset.corr())

    # sns.pairplot(dataset)
    # plt.show()
    # hi_set = []
    # hi_score = 0
    # for L in range(1, len(columns)+1):
    #     for subset in itertools.combinations(columns, L):
    #         print(list(subset))
    #         X = dataset[list(subset)]
    #         y = dataset[label]
    #
    #         X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=101)
    #
    #         lm = LinearRegression()
    #         lm.fit(X_train,y_train)
    #         predictions = lm.predict(X_test)
    #         score = r2_score(y_test,predictions)
    #         print(r2_score(y_test,predictions))
    #         if score > hi_score:
    #             hi_score = score
    #             hi_set = list(subset)
    #
    # print(hi_set)
    # print(hi_score)

    hi_set = ['Oswing', 'Zswing', 'Zcontact', 'Fstrike', 'SwStr', 'p_pa']
    scaler = MinMaxScaler()
    scaler.fit(dataset[hi_set])
    X_train = scaler.transform(dataset[hi_set])
    X_test = scaler.transform(statcast_2018[statcast_2018['pa'] >= 120][hi_set])
    # X = dataset[hi_set]
    y_train = dataset[label]
    y_test = statcast_2018[statcast_2018['pa'] >= 120][label]
    lm = Earth(max_degree=3, feature_importance_type='gcv')
    lm.fit(X_train,y_train)
    print(lm.feature_importances_)
    print(lm.trace())
    print(lm.summary())
    predictions = lm.predict(X_test)
    plt.scatter(y_test,predictions)
    print("Best:")
    print(r2_score(y_test,predictions))

    plt.show()

if __name__ == '__main__':
    get_xk_regression()
