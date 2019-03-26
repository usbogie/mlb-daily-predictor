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

statcast_2015 = pd.read_csv(os.path.join('data','projections','pitcher_statcast_2015.csv'))
statcast_2016 = pd.read_csv(os.path.join('data','projections','pitcher_statcast_2016.csv'))
statcast_2017 = pd.read_csv(os.path.join('data','projections','pitcher_statcast_2017.csv'))
statcast_2018 = pd.read_csv(os.path.join('data','projections','pitcher_statcast_2018.csv'))

def get_dataset(columns, label, year, thresh):
    if year == 2018:
        train = pd.concat([
            statcast_2017[statcast_2017['pa'] >= thresh],
            statcast_2016[statcast_2016['pa'] >= thresh],
            statcast_2015[statcast_2015['pa'] >= thresh],
        ])
        test = statcast_2018[statcast_2018['pa'] >= thresh]
    elif year == 2017:
        train = pd.concat([
            statcast_2018[statcast_2018['pa'] >= thresh],
            statcast_2016[statcast_2016['pa'] >= thresh],
            statcast_2015[statcast_2015['pa'] >= thresh],
        ])
        test = statcast_2017[statcast_2017['pa'] >= thresh]
    elif year == 2016:
        train = pd.concat([
            statcast_2018[statcast_2018['pa'] >= thresh],
            statcast_2017[statcast_2017['pa'] >= thresh],
            statcast_2015[statcast_2015['pa'] >= thresh],
        ])
        test = statcast_2016[statcast_2016['pa'] >= thresh]
    elif year == 2015:
        train = pd.concat([
            statcast_2018[statcast_2018['pa'] >= thresh],
            statcast_2017[statcast_2017['pa'] >= thresh],
            statcast_2016[statcast_2016['pa'] >= thresh],
        ])
        test = statcast_2015[statcast_2015['pa'] >= thresh]
    X_train = train[columns]
    y_train = train[label]
    X_test = test[columns]
    y_test = test[label]
    return X_train, y_train, X_test, y_test

def create_model(hi_set, X_train, y_train, X_test, y_test):
    scaler = MinMaxScaler()
    scaler.fit(X_train[hi_set])
    X_train = scaler.transform(X_train[hi_set])
    X_test = scaler.transform(X_test[hi_set])
    lm = Earth(max_degree=3, feature_importance_type='gcv')
    lm.fit(X_train,y_train)
    predictions = lm.predict(X_test)
    plt.scatter(y_test,predictions)
    # print(lm.feature_importances_)
    # print(lm.summary())
    # print(r2_score(y_test,predictions))
    return scaler, lm

def get_xk_regression(year):
    columns = [
        'Oswing','Zswing','swing','Ocontact','Zcontact','contact','zone',
        'Fstrike','SwStr','p_pa', 'LkStr', 'FlStr'
    ]
    label = 'k_pa'

    X_train, y_train, X_test, y_test = get_dataset(columns, label, year, 70)
    X_train['k_pa'] = y_train
    # print(X_train.corr())
    hi_set = ['Oswing', 'contact', 'SwStr', 'Fstrike', 'FlStr', 'LkStr', 'p_pa']
    scaler, lm = create_model(hi_set, X_train, y_train, X_test, y_test)

    # plt.show()
    return scaler, lm

def get_xbb_regression(year):
    columns = [
        'Oswing','Zswing','swing','Ocontact','Zcontact','contact','zone',
        'Fstrike','SwStr','p_pa', 'LkStr', 'FlStr'
    ]
    label = 'bb_pa'

    X_train, y_train, X_test, y_test = get_dataset(columns, label, year, 120)
    X_train['k_pa'] = y_train
    # print(X_train.corr())
    hi_set = ['swing', 'contact', 'zone', 'Fstrike', 'p_pa', 'LkStr', 'FlStr']
    scaler, lm = create_model(hi_set, X_train, y_train, X_test, y_test)

    # plt.show()
    return scaler, lm

if __name__ == '__main__':
    get_xk_regression()
