import os
import uuid

import pandas as pd
import fuzzywuzzy
from fuzzywuzzy import fuzz
from fuzzywuzzy import process


# save misc tools/functions here that are useful to have

# fuzzy merge for building mapping tables
def fuzzy_merge(df_1, df_2, key1, key2, threshold=80, limit=1):
    """
    :param df_1: the left table to join
    :param df_2: the right table to join
    :param key1: key column of the left table
    :param key2: key column of the right table
    :param threshold: how close the matches should be to return a match, based on Levenshtein distance
    :param limit: the amount of matches that will get returned, these are sorted high to low
    :return: dataframe with boths keys and matches
    """
    s = df_2[key2].tolist()

    m = df_1[key1].apply(lambda x: process.extract(x, s, limit=limit))
    df_1['matches'] = m

    m2 = df_1['matches'].apply(lambda x: ', '.join([i[0] for i in x if i[1] >= threshold]))
    df_1['matches'] = m2

    return df_1

# get mapping

# pull all box scores
dkpts_df = pd.DataFrame()
for file in os.listdir(r'data\raw\nba_box_score_stats'):
    print(file)
    df_box = pd.read_csv(r'data\raw\nba_box_score_stats' + '\\' + file, encoding='utf-8')[['slug', 'name', 'date_played', 'draftkings_points']]
    dkpts_df = dkpts_df.append(df_box)

# pull salaries
sal_df = pd.DataFrame()
for file in os.listdir(r'data\raw\draftkings_salaries'):
    print(file)
    df_s = pd.read_csv(r'data\raw\draftkings_salaries' + '\\' + file)
    sal_df = sal_df.append(df_s)

# mapping table
dkmap = dkpts_df[['slug', 'name']].drop_duplicates()
dkmap2 = sal_df[['ID', 'Name']].drop_duplicates()
mappingtable = fuzzy_merge(dkmap2, dkmap, key1='Name', key2='name')
mappingtable.drop('ID', axis=1, inplace=True)
mappingtable = mappingtable.drop_duplicates()
test = mappingtable.merge(dkmap, left_on='matches', right_on='name', how='left')

for i in test.Name:
    test.loc[test.Name==i, 'Player_ID'] = uuid.uuid3(uuid.NAMESPACE_DNS, i)

test.drop('matches', axis=1, inplace=True)
test.columns = ['DK_Name', 'BBR_slug', 'BBR_name', 'Player_ID']

test.to_csv(r'data\processed\mappingtable.csv')