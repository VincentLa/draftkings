import os

import pandas as pd
import numpy
from pulp import LpMaximize, LpProblem, LpStatus, lpSum, LpVariable

import src.util as ut
import src.prediction_models as pm
from src.injury_data import remove_injured_players
from src.dataclass import Player, Lineup
import yaml


# __file__ = r'C:\Users\Kevin\Documents\GitHub\draftkings\src\optimizer.py'
GIT_ROOT_DIR = ut.get_git_root(os.path.dirname(__file__))
DATA_DIR = os.path.join(GIT_ROOT_DIR, 'data')
DRAFTKINGS_SALARIES_DIR = os.path.join(DATA_DIR, 'raw', 'draftkings_salaries')
DRAFTKINGS_SALARIES_LIVE_DIR = os.path.join(DATA_DIR, 'raw', 'draftkings_salaries_live')
NBA_BOX_SCORE_DIR = os.path.join(DATA_DIR, 'raw', 'nba_box_score_stats')
PROBLEM_HISTORY_DIR = os.path.join(DATA_DIR, 'problem_history')
MAPPING_TABLE_FN = os.path.join(DATA_DIR, 'processed', 'player_map.csv')


def main():
    """
    Run Optimizer
    """
    config_path = os.path.join(PROBLEM_HISTORY_DIR, 'test.yaml')
    global config
    with open(config_path) as file:
        config = yaml.load(file)

    date = str(config.get('test_date'))
    testing_mode = config.get('testing_mode')

    # run mode
    if testing_mode == 'predict_run':
        predict_run(config, testing_mode, date, config_path)

    if testing_mode == 'backtest':
        None


def optimize(df):
    # optimize function - requires inputs in df, containing 'salary','position','EV' columns

    df['PG'] = df['position'].str.contains('PG')
    df['SG'] = df['position'].str.contains('SG')
    df['SF'] = df['position'].str.contains('SF')
    df['PF'] = df['position'].str.contains('PF')
    df['C'] = df['position'].str.contains('C')
    df['G'] = df['position'].str.contains('G')
    df['F'] = df['position'].str.contains('F')
    df['UTIL'] = df['position'].str.contains('UTIL')

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


    return model

def setup_opt_data(date, live_run, prediction_model, prediction_model_params, drop_inj):
    # import dfs stats and set up variable universe:
    if live_run:
        df = pd.read_csv(os.path.join(DRAFTKINGS_SALARIES_LIVE_DIR, 'dk_nba_salaries_classic_' + date + '.csv'))
    else:
        df = pd.read_csv(os.path.join(DRAFTKINGS_SALARIES_DIR, 'dk_nba_salaries_classic_' + date + '.csv'))

    # process live salary file to make column names consistent
    if 'Roster Position' in df.columns:
        df.rename(columns={'Roster Position': 'position'}, inplace=True)
    if 'Name' in df.columns:
        df.rename(columns={'Name': 'name'}, inplace=True)
    if 'Salary' in df.columns:
        df.rename(columns={'Salary': 'salary'}, inplace=True)
    df = df[~df.salary.isna()]

    # remove injured players - those labeled Doubtful or Out
    if drop_inj:
        df = remove_injured_players(df, date)

    # prediction model or actual boxscore
    if prediction_model=='boxscore':
        df_box = pd.read_csv(os.path.join(ut.NBA_BOX_SCORE_DIR, 'nba_box_score_stats_' + date + '.csv'))[
            ['slug', 'name', 'date_played', 'draftkings_points']]

        # merge this boxscore with salary df
        mapping_df = pd.read_csv(ut.MAPPING_TABLE_FN)
        test = df.merge(mapping_df, how='left', left_on='name', right_on='dk_name')
        test = test.merge(df_box, how='left', left_on='bbr_name', right_on='name')
        test = test.rename(columns={'draftkings_points': 'EV'})
        test.EV = test.EV.fillna(0)
        df = test

    # model recognition
    else:
        predict = getattr(pm, prediction_model)
        df = predict(df, optdate=date, games=prediction_model_params[0].get('games'))

    return df

def get_model_lineup(df, model, config_path):
    # convert model to lineup object
    playerlist = []
    for var in model.variables():
        if var.value() > 0:
            name = var.name[7:].replace("_", ' ')
            player_df = df[df.name == name]
            p = Player(name=name, position=player_df.position.values[0], player_id=player_df.player_id.values[0],
                       salary=player_df.salary.values[0], EV=player_df.EV.values[0], risk=None)
            print(var.name)
            playerlist.append(p)
    lineup = Lineup(mode=config.get('testing_mode'), date=str(config.get('test_date')), players=playerlist,
                    predict_model=config.get(config.get('testing_mode')).get('prediction_model'),
                    predict_model_params=config.get(config.get('testing_mode')).get('prediction_model_params'),
                    risk_model=None, risk_model_params=None, config=config_path)
    return lineup


def predict_run(config, testing_mode, date, config_path):
    df = setup_opt_data(date, live_run=config.get(testing_mode).get('draftkings_salaries_live'),
                        prediction_model=config.get(testing_mode).get('prediction_model'),
                        prediction_model_params=config.get(testing_mode).get('prediction_model_params'),
                        drop_inj=config.get(testing_mode).get('drop_injured_players'))
    model = optimize(df)

    lineup_obj = get_model_lineup(df, model, config_path)
    lineup_obj.calc_actual()

    # convert lineups to tables -
    lineup_obj.save(os.path.join(DATA_DIR, config.get('output_dir'),
                                 config.get(testing_mode).get('output_label') + '_' + date + '.xlsx'))
    return True


if __name__ == '__main__':
    """See https://stackoverflow.com/questions/419163/what-does-if-name-main-do"""
    main()

##### to update/not used currently
def best_possible_lineup(date):

    df = pd.read_csv(os.path.join(DRAFTKINGS_SALARIES_DIR, 'dk_nba_salaries_classic_' + date + '.csv'))
    df['PG'] = df['position'].str.contains('PG')
    df['SG'] = df['position'].str.contains('SG')
    df['SF'] = df['position'].str.contains('SF')
    df['PF'] = df['position'].str.contains('PF')
    df['C'] = df['position'].str.contains('C')
    df['G'] = df['position'].str.contains('G')
    df['F'] = df['position'].str.contains('F')
    df['UTIL'] = df['position'].str.contains('UTIL')

    df = df[~df.salary.isna()]

    # fill in boxscore
    df_box = pd.read_csv(os.path.join(NBA_BOX_SCORE_DIR, 'nba_box_score_stats_' + date + '.csv'))[['slug', 'name', 'date_played', 'draftkings_points']]
    mapping_df = pd.read_csv(MAPPING_TABLE_FN)
    test = df.merge(mapping_df, how='left', left_on='name', right_on='dk_name')
    test = test.merge(df_box, how='left', left_on='bbr_name', right_on='name')
    test = test.rename(columns={'draftkings_points': 'EV'})
    test = test.rename(columns={'name_x': 'name'})
    test.EV = test.EV.fillna(0)
    df = test

    model = LpProblem(name='dfs-nba', sense=LpMaximize)
    player_wgts = LpVariable.dicts('Player', df.name, lowBound=0, upBound=1, cat='Integer')

    # Add obj function
    model += lpSum(df[df.name == i].EV * player_wgts[i] for i in df.name)

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

    ret = pd.DataFrame(columns=[date])
    ret.loc[0,date] = model.objective.value()
    i = 1
    for var in model.variables():
        if var.value() > 0:
            print(f"{var.name}: {var.value()}")
            ret.loc[i,date] = var.name
            i=i+1
    return ret

def best_lineup_history():
    # buggy still - need to add try block
    df = pd.DataFrame()
    for file in os.listdir(DRAFTKINGS_SALARIES_DIR):
        df = pd.concat([df,best_possible_lineup(file[24:32])], axis=1)
    #df.to_csv(os.path.join(DATA_DIR, 'processed', 'best_lineup_history.csv'))