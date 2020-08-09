"""
Save misc tools/functions here that are useful to have
"""

import os
import uuid

import git
import pandas as pd
import fuzzywuzzy
from fuzzywuzzy import fuzz
from fuzzywuzzy import process


def get_git_root(path):
    """Return Top Level Git Repository directory given path"""
    git_repo = git.Repo(path, search_parent_directories=True)
    git_root = git_repo.git.rev_parse("--show-toplevel")
    return git_root


def check_missing_values(data):
    """Checks Missing Values By Column in a DataFrame"""
    df_count_missing = pd.DataFrame({
        'number_total_rows': data.shape[0],
        'number_missing_rows': data.isnull().sum(),
        'percentage': data.isnull().mean()})
    return df_count_missing


def fuzzy_merge(df_1, df_2, key1, key2, threshold=80, limit=1):
    """
    Fuzzy merge for building mapping tables

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