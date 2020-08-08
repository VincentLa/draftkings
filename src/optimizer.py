import os

import pandas as pd
import numpy
from pulp import LpMaximize, LpProblem, LpStatus, lpSum, LpVariable


# import dfs stats and set up variable universe:
df = pd.read_csv(r'data\raw\draftkings_salaries\DKNBASalaries_Classic_20200806.csv')
df['PG'] = df['Roster Position'].str.contains('PG')
df['SG'] = df['Roster Position'].str.contains('SG')
df['SF'] = df['Roster Position'].str.contains('SF')
df['PF'] = df['Roster Position'].str.contains('PF')
df['C'] = df['Roster Position'].str.contains('C')
df['G'] = df['Roster Position'].str.contains('G')
df['F'] = df['Roster Position'].str.contains('F')
df['UTIL'] = df['Roster Position'].str.contains('UTIL')

### Testing with boxscores
# import nba_box_scores and avg
dkpts_df = pd.DataFrame()
for file in os.listdir(r'data\raw\nba_box_score_stats'):
    df_box = pd.read_csv(r'data\raw\nba_box_score_stats' + '\\' + file)[['slug', 'name', 'date_played', 'draftkings_points']]
    dkpts_df = dkpts_df.append(df_box)

dkpts_df_avg = dkpts_df[['name', 'draftkings_points']].groupby('name').mean()

# # mapping table
# dkmap = dkpts_df[['slug', 'name']].drop_duplicates()
# dkmap2 = df[['ID', 'Name']].drop_duplicates()
# mappingtable = dkmap2.merge(dkmap, left_on='Name', right_on='name', how='outer')
# mappingtable.to_csv('mappingtable.csv')

mapping_df = pd.read_csv('mappingtable.csv', index_col=0)[['ID', 'slug', 'name']]
test = df.merge(mapping_df, on='ID', how='left')
test = test.merge(dkpts_df_avg, on='name', how='left')
test = test.drop('AvgPointsPerGame', axis=1)
test = test.rename(columns={'draftkings_points':'AvgPointsPerGame'})
test.AvgPointsPerGame = test.AvgPointsPerGame.fillna(0)

df = test

model = LpProblem(name='dfs-nba', sense=LpMaximize)
player_wgts = LpVariable.dicts("Player",df.Name,lowBound=0,upBound=1,cat='Integer')

# Add obj function
model += lpSum(df[df.Name == i].AvgPointsPerGame*player_wgts[i] for i in df.Name)

# set up model constraints
model += (lpSum(df[df.Name == i].Salary*player_wgts[i] for i in df.Name) <= 50000, 'Salary constraint')
model += (lpSum(player_wgts[i] for i in df.Name) == 8, 'Player constraint')
model += (lpSum(df[df.Name == i].PG*player_wgts[i] for i in df.Name) >= 1, 'PG constraint')
model += (lpSum(df[df.Name == i].SG*player_wgts[i] for i in df.Name) >= 1, 'SG constraint')
model += (lpSum(df[df.Name == i].SF*player_wgts[i] for i in df.Name) >= 1, 'SF constraint')
model += (lpSum(df[df.Name == i].PF*player_wgts[i] for i in df.Name) >= 1, 'PF constraint')
model += (lpSum(df[df.Name == i].C*player_wgts[i] for i in df.Name) >= 1, 'C constraint')
model += (lpSum(df[df.Name == i].G*player_wgts[i] for i in df.Name) >= 3, 'G constraint')
model += (lpSum(df[df.Name == i].F*player_wgts[i] for i in df.Name) >= 3, 'F constraint')

status = model.solve()

print(f"status: {model.status}, {LpStatus[model.status]}")

print(f"objective: {model.objective.value()}")

for var in model.variables():
    if var.value() > 0:
        print(f"{var.name}: {var.value()}")

for name, constraint in model.constraints.items():
    print(f"{name}: {constraint.value()}")

model.to_json('data/problem_history/20200806_problem.json')