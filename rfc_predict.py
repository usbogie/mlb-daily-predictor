import pandas as pd
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import make_classification

df = pd.concat([pd.read_csv(os.path.join('data','RFC_input','2017.csv')),pd.read_csv(os.path.join('data','RFC_input','2016.csv'))])

xL_v_L = df[df['matchup'] == 'L_v_L'][['p_ld','p_gb','p_fb','b_hr','b_ld','b_gb','b_fb']]
xR_v_L = df[df['matchup'] == 'R_v_L'][['p_ld','p_gb','p_fb','b_hr','b_ld','b_gb','b_fb']]
xL_v_R = df[df['matchup'] == 'L_v_R'][['p_ld','p_gb','p_fb','b_hr','b_ld','b_gb','b_fb']]
xR_v_R = df[df['matchup'] == 'R_v_R'][['p_ld','p_gb','p_fb','b_hr','b_ld','b_gb','b_fb']]
xL_v_L = xL_v_L.values
xR_v_L = xR_v_L.values
xL_v_R = xL_v_R.values
xR_v_R = xR_v_R.values


yL_v_L = df[df['matchup'] == 'L_v_L'][['res_1b','res_xbh','res_hr','res_out']]
yR_v_L = df[df['matchup'] == 'R_v_L'][['res_1b','res_xbh','res_hr','res_out']]
yL_v_R = df[df['matchup'] == 'L_v_R'][['res_1b','res_xbh','res_hr','res_out']]
yR_v_R = df[df['matchup'] == 'R_v_R'][['res_1b','res_xbh','res_hr','res_out']]
yL_v_L = yL_v_L.values
yR_v_L = yR_v_L.values
yL_v_R = yL_v_R.values
yR_v_R = yR_v_R.values

clf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=0)
clf.fit(xL_v_L, yL_v_L)
print(list(zip(['p_hr', 'p_ld','p_gb','p_fb','b_hr','b_ld','b_gb','b_fb'], clf.feature_importances_)))

clf.fit(xR_v_L, yR_v_L)
print(list(zip(['p_hr', 'p_ld','p_gb','p_fb','b_hr','b_ld','b_gb','b_fb'], clf.feature_importances_)))

clf.fit(xL_v_R, yL_v_R)
print(list(zip(['p_hr', 'p_ld','p_gb','p_fb','b_hr','b_ld','b_gb','b_fb'], clf.feature_importances_)))

clf.fit(xR_v_R, yR_v_R)
print(list(zip(['p_hr', 'p_ld','p_gb','p_fb','b_hr','b_ld','b_gb','b_fb'], clf.feature_importances_)))
