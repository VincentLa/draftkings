import pandas as pd
import numpy
from pulp import LpMaximize, LpProblem, LpStatus, lpSum, LpVariable

model = LpProblem(name='dfs-nba', sense=LpMaximize)

# import dfs stats and set up variable universe:
df = pd.read_csv(r'data\raw\draftkings_salaries\DKNBASalaries_20200806.csv')
df['PG'] = df['Roster Position'].str.contains('PG')
df['SG'] = df['Roster Position'].str.contains('SG')
df['SF'] = df['Roster Position'].str.contains('SF')
df['PF'] = df['Roster Position'].str.contains('PF')
df['C'] = df['Roster Position'].str.contains('C')
df['G'] = df['Roster Position'].str.contains('G')
df['F'] = df['Roster Position'].str.contains('F')
df['UTIL'] = df['Roster Position'].str.contains('UTIL')

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

# solver info
model.solver