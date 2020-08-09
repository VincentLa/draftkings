"""
Creates a player mapping table across the difference data sources

-- Draft Kings
-- Basketball Reference
-- NBA Injury Data (Eventually)
"""
import os
import uuid

import pandas as pd

import src.util as ut

GIT_ROOT_DIR = ut.get_git_root(os.path.dirname(__file__))
DATA_DIR = os.path.join(GIT_ROOT_DIR, 'data')
PROCESSED_DATA_DIR = os.path.join(GIT_ROOT_DIR, 'data', 'processed')
NBA_BOX_SCORE_DIR = os.path.join(DATA_DIR, 'raw', 'nba_box_score_stats')
DRAFTKINGS_SALARIES_DIR = os.path.join(DATA_DIR, 'raw', 'draftkings_salaries')


def create_player_mapping():
    """
    Creates Player Map
    """
    # Pulling All Box Scores
    print('Reading All Box Scores')
    dkpts_df = pd.DataFrame()
    for file in os.listdir(NBA_BOX_SCORE_DIR):
        df_box = pd.read_csv(os.path.join(NBA_BOX_SCORE_DIR, file), encoding='utf-8')[['slug', 'name', 'date_played', 'draftkings_points']]
        dkpts_df = dkpts_df.append(df_box)

    # Pull DraftKings Salaries
    print('Reading all DraftKings Salaries')
    sal_df = pd.DataFrame()
    for file in os.listdir(DRAFTKINGS_SALARIES_DIR):
        df_s = pd.read_csv(os.path.join(DRAFTKINGS_SALARIES_DIR, file))
        sal_df = sal_df.append(df_s)

    # mapping table
    print('Creating Mapping Table')
    dkmap = dkpts_df[['slug', 'name']].drop_duplicates()
    dkmap2 = sal_df[['name']].drop_duplicates()
    mappingtable = ut.fuzzy_merge(dkmap2, dkmap, key1='name', key2='name')
    mappingtable = mappingtable.drop_duplicates()
    player_map_df = mappingtable.merge(dkmap, left_on='matches', right_on='name', how='left')

    for i in player_map_df.Name:
        player_map_df.loc[player_map_df.Name==i, 'Player_ID'] = uuid.uuid3(uuid.NAMESPACE_DNS, i)

    player_map_df.drop('matches', axis=1, inplace=True)
    player_map_df.columns = ['dk_name', 'bbr_slug', 'bbr_name', 'player_id']

    player_map_df.to_csv(os.path.join(PROCESSED_DATA_DIR, 'mappingtable.csv'), index=False)


def main():
    """
    Run Player Mapping
    """
    print('Creating Player Map')
    create_player_mapping()


if __name__ == '__main__':
    """See https://stackoverflow.com/questions/419163/what-does-if-name-main-do"""
    main()
