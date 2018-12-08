import pandas as pd
import os
from itertools import combinations, groupby
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import classification_report,confusion_matrix,r2_score, mean_squared_error
from sklearn.neural_network import MLPRegressor
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import RandomizedSearchCV
from sklearn.linear_model import LinearRegression
from sklearn.externals import joblib

import warnings
warnings.filterwarnings(action="ignore", message="^internal gelsd")
warnings.filterwarnings(action="ignore", category=FutureWarning)
warnings.filterwarnings(action="ignore", category=RuntimeWarning)
warnings.filterwarnings(action="ignore", category=UserWarning)

# feature_headers = ['p_hr','p_ld','p_gb','p_fb','p_so','p_bb','p_hbp',
#                    'b_hr','b_ld','b_gb','b_fb','b_so','b_bb','b_hbp']

df = pd.concat([pd.read_csv(os.path.join('data','RFC_input','2015.csv')),
                pd.read_csv(os.path.join('data','RFC_input','2016.csv')),
                pd.read_csv(os.path.join('data','RFC_input','2017.csv'))])

# feature_headers = ['p_so', 'p_bb', 'p_hbp', 'b_so', 'b_bb', 'b_hbp', 'b_fb', 'b_hr', 'b_ld', 'p_fb', 'p_gb', 'p_hr']
# target_header = 'res_so'
# savestring = '{}so.save'

# feature_headers =  ['p_so', 'p_bb', 'p_hbp', 'b_so', 'b_bb', 'b_hbp', 'b_fb']
# target_header = 'res_bbhbp'
# savestring = '{}bbhbp.save'

# feature_headers = ['p_hr', 'b_hr', 'p_fb', 'b_fb', 'b_gb', 'b_ld', 'b_so', 'p_bb', 'p_gb', 'p_so']
# target_header = 'res_hr'
# savestring = '{}hr.save'

# feature_headers = ['p_ld', 'p_gb', 'p_fb', 'b_ld', 'b_gb', 'b_fb', 'b_bb',
#                    'b_hbp', 'b_so', 'p_bb', 'p_hbp', 'p_hr', 'p_so']
# target_header = 'res_hit'
# savestring = '{}hit.save'
#
feature_headers = ['p_ld', 'p_gb', 'p_fb', 'b_ld', 'b_gb', 'b_fb', 'b_bb', 'b_hr', 'b_so', 'p_hr', 'p_so']
target_header = 'res_out'
savestring = '{}out.save'

def split_dataset(dataset, train_percentage):
    train_x, test_x, train_y, test_y = train_test_split(dataset[feature_headers],
                                                        dataset[target_header],
                                                        train_size=train_percentage)
    return train_x, test_x, train_y, test_y

def scale_data(trainX, testX):
    scaler = StandardScaler().fit(trainX)
    trainX = scaler.transform(trainX)
    testX = scaler.transform(testX)
    return trainX, testX, scaler

hyperparameters = [
    {
        'activation': ['identity', 'logistic'],
        'learning_rate': ['constant', 'adaptive'],
        'solver': ['lbfgs', 'sgd', 'adam'],
    },
    {}
]

ml_scaler_path = os.path.join('saved_ml_files', 'scalers')
mlp_path = os.path.join('saved_ml_files', 'regressors')

def run(clf, i, X, y, trainX, trainY, testX, testY, name):

    print("fitting randomCV")
    clf = RandomizedSearchCV(clf,hyperparameters[i],cv=5,n_jobs=-1).fit(trainX, trainY)
    print(clf.best_estimator_)

    clf = clf.best_estimator_
    joblib.dump(clf, os.path.join(mlp_path,savestring.format(name)))

    print("getting r2 scores")
    scores = cross_val_score(clf, X, y, cv=5, scoring='r2',n_jobs=-1)
    print(scores)

    preds = clf.predict(testX)
    print(r2_score(testY, preds), mean_squared_error(testY, preds))

algos = [
    MLPRegressor(),
    #LinearRegression(),
]

for matchup in ['L_v_L', 'R_v_L', 'L_v_R', 'R_v_R']:
    train_x, test_x, train_y, test_y = split_dataset(df[df['matchup'] == matchup], .725)
    train_x, test_x, scaler = scale_data(train_x, test_x)
    joblib.dump(scaler, os.path.join(ml_scaler_path,savestring.format(matchup)))
    for i, algorithm in enumerate(algos):
        print(matchup)
        # combos = []
        # for x in range(len(feature_headers)):
        #     for comb in list(combinations(feature_headers, x)):
        #         combos.append(sorted(comb))
        # combos.sort()
        # print(len(list(k for k,_ in groupby(combos))))
        # for comb in list(k for k,_ in groupby(combos)):
        #     x = ['p_ld','p_gb','p_fb','b_ld','b_gb','b_fb'] + list(comb)
        #     train_x, test_x, train_y, test_y = split_dataset(df[df['matchup'] == matchup], .7, feature_headers=x)
        #     print(x)
        #     run(algorithm, i, df[x].as_matrix(), df[target_header].as_matrix(), train_x, train_y, test_x, test_y, matchup)
        run(algorithm, i, df[feature_headers].as_matrix(), df[target_header].as_matrix(), train_x, train_y, test_x, test_y, matchup)
