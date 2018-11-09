import pandas as pd
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import make_classification

df = pd.concat([pd.read_csv(os.path.join('data','RFC_input','2017.csv')),pd.read_csv(os.path.join('data','RFC_input','2016.csv'))])

X = df[['p_ld','p_gb','p_fb','b_hr','b_ld','b_gb','b_fb']]
X = X.values
y = df[['res_1b','res_xbh','res_hr','res_out']]
y = y.values
clf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=0)
clf.fit(X, y)
print(list(zip(['p_ld','p_gb','p_fb','b_hr','b_ld','b_gb','b_fb'], clf.feature_importances_)))
