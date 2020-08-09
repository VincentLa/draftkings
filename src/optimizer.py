import os

import pandas as pd
import numpy
from pulp import LpMaximize, LpProblem, LpStatus, lpSum, LpVariable

import src.util as ut
import src.prediction_models as pm

# __file__ = r'C:\Users\Kevin\Documents\GitHub\draftkings\src\optimizer.py'
GIT_ROOT_DIR = ut.get_git_root(os.path.dirname(__file__))
DATA_DIR = os.path.join(GIT_ROOT_DIR, 'data')
DRAFTKINGS_SALARIES_DIR = os.path.join(DATA_DIR, 'raw', 'draftkings_salaries')
NBA_BOX_SCORE_DIR = os.path.join(DATA_DIR, 'raw', 'nba_box_score_stats')
PROBLEM_HISTORY_DIR = os.path.join(DATA_DIR, 'problem_history')
MAPPING_TABLE_FN = os.path.join(DATA_DIR, 'processed', 'player_map.csv')


def main():
    """
    Run Optimizer
    """
    date = '20200806'

    # import dfs stats and set up variable universe:
    df = pd.read_csv(os.path.join(DRAFTKINGS_SALARIES_DIR, 'dk_nba_salaries_classic_' + date + '.csv'))
    df['PG'] = df['position'].str.contains('PG')
    df['SG'] = df['position'].str.contains('SG')
    df['SF'] = df['position'].str.contains('SF')
    df['PF'] = df['position'].str.contains('PF')
    df['C'] = df['position'].str.contains('C')
    df['G'] = df['position'].str.contains('G')
    df['F'] = df['position'].str.contains('F')
    df['UTIL'] = df['position'].str.contains('UTIL')

    df = pm.recent_mean(df, optdate=date)
    df = df[~df.salary.isna()]

    model = LpProblem(name='dfs-nba', sense=LpMaximize)
    player_wgts = LpVariable.dicts('Player', df.name, lowBound=0, upBound=1, cat='Integer')

    # Add obj function
    model += lpSum(df[df.name == i].EV*player_wgts[i] for i in df.name)

    # set up model constraints
    model += (lpSum(df[df.name == i].salary * player_wgts[i] for i in df.name) <= 50000, 'Salary constraint')
    model += (lpSum(player_wgts[i] for i in df.name) == 8, 'Player constraint')
    model += (lpSum(df[df.name == i].PG * player_wgts[i] for i in df.name) >= 1, 'PG constraint')
    model += (lpSum(df[df.name == i].SG * player_wgts[i] for i in df.name) >= 1, 'SG constraint')
    model += (lpSum(df[df.name == i].SF * player_wgts[i] for i in df.name) >= 1, 'SF constraint')
    model += (lpSum(df[df.name == i].PF * player_wgts[i] for i in df.name) >= 1, 'PF constraint')
    model += (lpSum(df[df.name == i].C * player_wgts[i] for i in df.name) >= 1, 'C constraint')
    model += (lpSum(df[df.name == i].G * player_wgts[i] for i in df.name) >= 3, 'G constraint')
    model += (lpSum(df[df.name == i].F * player_wgts[i] for i in df.name) >= 3, 'F constraint')

    status = model.solve()

    print(f"status: {model.status}, {LpStatus[model.status]}")

    print(f"objective: {model.objective.value()}")

    for var in model.variables():
        if var.value() > 0:
            print(f"{var.name}: {var.value()}")

    for name, constraint in model.constraints.items():
        print(f"{name}: {constraint.value()}")

    model.to_json(os.path.join(PROBLEM_HISTORY_DIR, 'test_problem.json'))

if __name__ == '__main__':
    """See https://stackoverflow.com/questions/419163/what-does-if-name-main-do"""
    main()


