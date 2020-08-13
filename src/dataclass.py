import numpy as np
import pandas as pd
import uuid
import datetime
import pickle
import os
import yaml
import src.util as ut

# data classes to store data with player-lineup structure

class Player:
    def __init__(self, name, player_id, position, salary, EV, risk):
        self.name = name
        self.player_id = player_id # player id that matches mapping table id
        self.position = position
        self.salary = salary
        self.EV = EV
        self.risk = risk
        self.actual = None

class Lineup:
    def __init__(self, mode, date, players, predict_model, predict_model_params, risk_model, risk_model_params, config):
        self.id = uuid.uuid4() #create id on lineup creation
        self.mode = mode
        self.date = date
        self.run_datetime = datetime.datetime.now()
        self.players = players #list of players
        self.predict_model = predict_model
        self.predict_model_params = predict_model_params
        self.risk_model = risk_model
        self.risk_model_params = risk_model_params
        self.config = config
        self.lineup_EV = self.calc_EV()
        self.lineup_actual = None

    def add(self, p):
        self.players.append(p)

    def remove(self, p):
        self.players.remove(p)

    def calc_EV(self):
        pts = 0
        for p in self.players:
            pts = pts + p.EV
        self.lineup_EV = pts
        return pts

    def calc_actual(self):
        if os.path.exists(os.path.join(ut.NBA_BOX_SCORE_DIR, 'nba_box_score_stats_' + self.date + '.csv')):
            box_df = pd.read_csv(os.path.join(ut.NBA_BOX_SCORE_DIR, 'nba_box_score_stats_' + self.date + '.csv'))
            mapping_df = pd.read_csv(ut.MAPPING_TABLE_FN)
            box_df = box_df.merge(mapping_df[['bbr_slug', 'player_id']], left_on='slug', right_on='bbr_slug')
            pts = 0
            for p in self.players:
                player_fp=0
                if len(box_df[box_df.player_id == p.player_id]['draftkings_points']) > 0:
                    player_fp = box_df[box_df.player_id == p.player_id]['draftkings_points'].values[0]
                    pts = pts + player_fp
                p.actual = player_fp
            self.lineup_actual = pts
        return

    def save(self, path):
        lineup_df = pd.DataFrame(columns=['lineup_id', 'date', 'mode', 'run_date', 'players', 'predict_model', 'predict_model_params', 'risk_model', 'risk_model_params', 'configs', 'EV', 'actual'])
        players_df = pd.DataFrame(columns=['lineup_id', 'date', 'run_date', 'name', 'player_id', 'position', 'salary', 'EV', 'risk', 'actual'])

        playerlist=[]
        for p in self.players:
            playerlist.append(p.name)
            players_df = players_df.append({'lineup_id':self.id, 'date':self.date, 'run_date':self.run_datetime,
                                            'name': p.name, 'player_id':p.player_id, 'position':p.position,
                                            'salary':p.salary, 'EV':p.EV, 'risk':p.risk, 'actual':p.actual}, ignore_index=True)

        lineup_df = lineup_df.append({'lineup_id':self.id, 'date':self.date, 'mode':self.mode, 'run_date':self.run_datetime,
                                      'players':playerlist, 'predict_model':self.predict_model, 'predict_model_params':self.predict_model_params,
                                      'risk_model':self.risk_model, 'risk_model_params':self.risk_model_params,
                                      'configs':self.config, 'EV':self.lineup_EV, 'actual':self.lineup_actual}, ignore_index=True)

        with open(self.config) as file:
            config = yaml.load(file)


        if os.path.exists(path):
            temp_df = pd.read_excel(path, sheet_name='lineup', index_col=0)
            lineup_df = temp_df.append(lineup_df)
            temp_df = pd.read_excel(path, sheet_name='players', index_col=0)
            players_df = temp_df.append(players_df)

        writer = pd.ExcelWriter(path)
        lineup_df.to_excel(writer, sheet_name='lineup')
        players_df.to_excel(writer, sheet_name='players')
        writer.save()

        testing_mode = config.get('testing_mode')
        if (config.get(testing_mode).get('save_to_db') == True):
            None
            # save to db here

        return