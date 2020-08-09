import os

import pandas as pd
import numpy
from pulp import LpMaximize, LpProblem, LpStatus, lpSum, LpVariable

import src.util as ut

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
    # import dfs stats and set up variable universe:
    df = pd.read_csv(os.path.join(DRAFTKINGS_SALARIES_DIR, 'dk_nba_salaries_classic_20200806.csv'))
    df['PG'] = df['position'].str.contains('PG')
    df['SG'] = df['position'].str.contains('SG')
    df['SF'] = df['position'].str.contains('SF')
    df['PF'] = df['position'].str.contains('PF')
    df['C'] = df['position'].str.contains('C')
    df['G'] = df['position'].str.contains('G')
    df['F'] = df['position'].str.contains('F')
    df['UTIL'] = df['position'].str.contains('UTIL')

    ### Testing with boxscores
    # import nba_box_scores and avg
    dkpts_df = pd.DataFrame()
    for file in os.listdir(NBA_BOX_SCORE_DIR):
        df_box = pd.read_csv(os.path.join(NBA_BOX_SCORE_DIR, file))[['slug', 'name', 'date_played', 'draftkings_points']]
        dkpts_df = dkpts_df.append(df_box)

    dkpts_df_avg = dkpts_df[['name', 'draftkings_points']].groupby('name').mean()


    mapping_df = pd.read_csv(MAPPING_TABLE_FN)
    test = df.merge(mapping_df, how='left', left_on='name', right_on='dk_name')
    test = test.merge(dkpts_df_avg, how='left', left_on='bbr_name', right_on='name')
    #test = test.drop('AvgPointsPerGame', axis=1)
    test = test.rename(columns={'draftkings_points':'AvgPointsPerGame'})
    test.AvgPointsPerGame = test.AvgPointsPerGame.fillna(0)

    df = test
    df = df[~df.salary.isna()]

    model = LpProblem(name='dfs-nba', sense=LpMaximize)
    player_wgts = LpVariable.dicts('Player', df.name, lowBound=0, upBound=1, cat='Integer')

    # Add obj function
    model += lpSum(df[df.name == i].AvgPointsPerGame*player_wgts[i] for i in df.name)

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


