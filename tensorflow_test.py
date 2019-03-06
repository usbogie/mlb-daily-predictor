from __future__ import absolute_import, division, print_function

import os
import pathlib
import itertools

import pandas as pd
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt

import talos as ta
from talos.model.early_stopper import early_stopper
from talos.model.normalizers import lr_normalizer

import tensorflow as tf
from tensorflow import keras

from keras.activations import softmax, sigmoid, relu, elu
from keras.layers import Dropout, Dense
from keras.losses import logcosh, mean_absolute_error, mean_squared_error
from keras.models import Sequential
from keras.optimizers import Adam, Nadam, RMSprop
from keras.regularizers import l1,l2

tf.logging.set_verbosity(tf.logging.INFO)

input_2015 = pd.read_csv(os.path.join('data','tensor_inputs','2015.csv'))
input_2016 = pd.read_csv(os.path.join('data','tensor_inputs','2016.csv'))
input_2017 = pd.read_csv(os.path.join('data','tensor_inputs','2017.csv'))
input_2018 = pd.read_csv(os.path.join('data','tensor_inputs','2018.csv'))

COLUMNS = ['b1','b2','b3','b4','b5','b6','b7','b8','b9','pitching','runs_scored']
train_dataset = pd.concat([
    input_2015[COLUMNS],
    input_2016[COLUMNS],
    input_2017[COLUMNS],
])

test_dataset = input_2018[COLUMNS]

# sns.pairplot(train_dataset[COLUMNS], diag_kind="kde")
# plt.show()

train_stats = train_dataset.describe()
train_stats.pop('runs_scored')
train_stats = train_stats.transpose()
y = train_dataset.pop('runs_scored')
test_labels = test_dataset.pop('runs_scored')

def norm(x):
    return (x - train_stats['mean']) / train_stats['std']

normed_x = norm(train_dataset)
normed_test_data = norm(test_dataset)

p = {'lr': [0.1, 0.01],
     'first_neuron':[16, 64, 256],
     'second_neuron':[16, 64, 256],
     'dropout1': [0, 0.20, 0.5],
     'dropout2': [0, 0.20, 0.5],
     'optimizer': [Adam, RMSprop],
     'first_activation': [relu, softmax, sigmoid],
     'last_activation': [relu],
     'second_activation': [relu, softmax, sigmoid],
     'weight_regulizer': [None,l1,l2]}

def runs_model(x_train, y_train, x_val, y_val, params):
    print(y_train.shape[1])
    model = Sequential()
    model.add(Dense(params['first_neuron'],
                    input_dim=x_train.shape[1],
                    activation=params['first_activation']))
    model.add(Dropout(params['dropout1']))
    model.add(Dense(params['second_neuron'],
                    input_dim=x_train.shape[1],
                    activation=params['second_activation']))
    model.add(Dropout(params['dropout2']))
    model.add(Dense(y_train.shape[1],activation=params['last_activation']))

    model.compile(optimizer=params['optimizer'](lr=lr_normalizer(params['lr'], params['optimizer'])),
                  loss=mean_squared_error,
                  metrics=['mae', 'mse'])

    out = model.fit(x_train, y_train,
                    validation_split=.4,
                    batch_size=50,
                    epochs=1000,
                    verbose=0,
                    validation_data=[x_val, y_val],
                    callbacks=[early_stopper(1000, mode='strict')])

    return (out, model)

h = ta.Scan(x=normed_x.values,y=y.values.reshape(len(y),1),
            params=p,
            model=runs_model,
            dataset_name='runs_scored',
            experiment_no='1',
            grid_downsample=.01)

# accessing the results data frame
print('DATA HEAD')
print(h.data.head())

# accessing epoch entropy values for each round
print('EPOCHS DF')
print(h.peak_epochs_df)

# access the summary details
print('SUMMARY DETAILS')
print(h.details)

r = ta.Reporting(h)

# get the number of rounds in the Scan
print('ROUNDS in Scan')
print(r.rounds())

# get the highest result ('val_acc' by default)
print('Highest val_acc')
print(r.high())

# get the highest result for any metric
print('Highest result for any metrics')
print(r.high('acc'))

# get the round with the best result
print('Highest round result')
print(r.rounds2high())

# get the best paramaters
print('Best parameters')
print(r.best_params())

# # get correlation for hyperparameters against a metric
# print('Loss correlation')
# print(r.correlate('loss'))

# # a regression plot for two dimensions
# r.plot_regs()
#
# # line plot
# r.plot_line()
#
# # up to two dimensional kernel density estimator
# r.plot_kde('val_acc')
#
# # a simple histogram
# r.plot_hist(bins=50)
#
# # heatmap correlation
# r.plot_corr()
#
# # a four dimensional bar grid
# r.plot_bars('batch_size', 'val_acc', 'first_neuron', 'lr')
# plt.show()

e = ta.Evaluate(h)
print('Evaluation:')
print(e.evaluate(normed_x.values, y.values.reshape(len(y),1), folds=10, average='macro'))

# print(h.predict(normed_test_data.values, test_labels.values.reshape(len(y),1)))

ta.Deploy(h, 'runs_model')
runs_model = ta.Restore('runs_model.zip')
print('Predict')
print([x[0] for x in list(runs_model.model.predict(normed_test_data.values))])

print('Details:')
print(runs_model.details)
print('params:')
print(runs_model.params)
print('x:')
print(runs_model.x)
print('y:')
print(runs_model.y)
print('Results:')
print(runs_model.results)
