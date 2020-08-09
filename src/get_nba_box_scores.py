"""
Script to grab NBA Box Score Data

To run, cd into the root level directory of this repo. For example, run:

python -m src.get_nba_box_scores --start_game_year=2019 --start_game_month=10 --start_game_day=22 --end_game_year=2020 --end_game_month=8 --end_game_day=7

To run a single day, set the start and end dates to be the same
"""

import argparse
import datetime as dt
import os
from pathlib import Path
import sys

import basketball_reference_web_scraper
from basketball_reference_web_scraper import client
import git
import pandas as pd

import src.util as ut


GIT_ROOT_DIR = ut.get_git_root(os.getcwd())
DATA_DIR = os.path.join(GIT_ROOT_DIR, 'data')

# Constants to translate raw NBA stats to DraftKings Points.
# Pulling them out here in case they change it's easy to swap out
POINTS_MULTIPLE = 1
THREE_POINT_MULTIPLE = 0.5
REBOUND_MULTIPLE = 1.25
ASSIST_MULTIPLE = 1.5
STEAL_MULTIPLE = 2
BLOCK_MULTIPLE = 2
TURNOVER_MULTIPLE = -0.5
DOUBLE_DOUBLE_MULTIPLE = 1.5
TRIPLE_DOUBLE_MULTIPLE = 3

HELP_TEXT = """
This is a runner to get NBA box score data. We are largely depending on the following package: https://jaebradley.github.io/basketball_reference_web_scraper/api/.

You need to specify a range, if you only want one day of data, you can just specify the same date for both the start and end date
"""


def get_args():
    """Use argparse to parse command line arguments."""
    parser = argparse.ArgumentParser(description=HELP_TEXT)
    parser.add_argument(
        '--start_game_year',
        help='Start Year Range',
        type=int,
        required=True
    )
    parser.add_argument(
        '--start_game_month',
        help='Start Month Range',
        type=int,
        required=True

    )
    parser.add_argument(
        '--start_game_day',
        help='Start Day Range',
        type=int,
        required=True
    )
    parser.add_argument(
        '--end_game_year',
        help='End Year Range',
        type=int,
        required=True
    )
    parser.add_argument(
        '--end_game_month',
        help='End Month Range',
        type=int,
        required=True

    )
    parser.add_argument(
        '--end_game_day',
        help='End Day Range',
        type=int,
        required=True
    )
    return parser.parse_args()


def get_player_box_scores_day(game_year, game_month, game_day):
    """
    Get all player box scores for a given day. Scraped from Basketball Reference
    
    Keyword Args:
      - game_year: integer, year of game
      - game_month: integer, month of game
      - game_day: integer, day of game
      
    We are using a package: https://jaebradley.github.io/basketball_reference_web_scraper/api/
    """
    player_box_scores = client.player_box_scores(day=game_day, month=game_month, year=game_year)
    
    if len(player_box_scores) == 0:
        print('There were no games played on date: {}-{}-{}'.format(
            game_year, str(game_month).rjust(2, '0'), str(game_day).rjust(2, '0')))
        return None
    
    player_box_scores_df = pd.DataFrame(player_box_scores)
    player_box_scores_df['date_played'] = dt.date(game_year, game_month, game_day)
    player_box_scores_df['total_rebounds'] = player_box_scores_df['offensive_rebounds'] + player_box_scores_df['defensive_rebounds']
    player_box_scores_df['total_points_scored'] = (player_box_scores_df['made_field_goals'] - player_box_scores_df['made_three_point_field_goals']) * 2 \
        + player_box_scores_df['made_three_point_field_goals'] * 3 \
        + player_box_scores_df['made_free_throws']
    player_box_scores_df['total_double_digit_stats'] = (player_box_scores_df['total_points_scored'] >= 10).astype(int) \
        + (player_box_scores_df['total_rebounds'] >= 10).astype(int) \
        + (player_box_scores_df['assists'] >= 10).astype(int) \
        + (player_box_scores_df['steals'] >= 10).astype(int) \
        + (player_box_scores_df['blocks'] >= 10).astype(int)
    player_box_scores_df['double_double_flag'] = (player_box_scores_df['total_double_digit_stats'] == 2).astype(int)
    player_box_scores_df['triple_double_flag'] = (player_box_scores_df['total_double_digit_stats'] >= 3).astype(int)
    
    player_box_scores_df['draftkings_points'] = \
        POINTS_MULTIPLE * player_box_scores_df['total_points_scored'] \
        + THREE_POINT_MULTIPLE * player_box_scores_df['made_three_point_field_goals'] \
        + REBOUND_MULTIPLE * player_box_scores_df['total_rebounds'] \
        + ASSIST_MULTIPLE * player_box_scores_df['assists'] \
        + STEAL_MULTIPLE * player_box_scores_df['steals'] \
        + BLOCK_MULTIPLE * player_box_scores_df['blocks'] \
        + TURNOVER_MULTIPLE * player_box_scores_df['turnovers'] \
        + DOUBLE_DOUBLE_MULTIPLE * player_box_scores_df['double_double_flag'] \
        + TRIPLE_DOUBLE_MULTIPLE * player_box_scores_df['triple_double_flag']
    
    player_box_scores_df = player_box_scores_df[[
        'slug',
        'name',
        'team',
        'location',
        'opponent',
        'date_played',
        'outcome',
        'seconds_played',
        'made_field_goals',
        'attempted_field_goals',
        'made_three_point_field_goals',
        'attempted_three_point_field_goals',
        'made_free_throws',
        'attempted_free_throws',
        'total_points_scored',
        'total_rebounds',
        'assists',
        'steals',
        'blocks',
        'turnovers',
        'double_double_flag',
        'triple_double_flag',
        'draftkings_points',    
    ]]
    
    player_box_scores_df.sort_values('draftkings_points', ascending=False, inplace=True)
    
    filename = os.path.join(
        DATA_DIR, 'raw', 'nba_box_score_stats', 'nba_box_score_stats_{}{}{}.csv'.format(
            game_year, str(game_month).rjust(2, '0'), str(game_day).rjust(2, '0')))
    
    print('Writing file: {}'.format(filename))
    player_box_scores_df.to_csv(filename, index=False, encoding='utf-8')
    
    return player_box_scores_df
    

def main():
    """
    Run Getting NBA Box Scores
    """
    args = get_args()
    start_game_year = args.start_game_year
    start_game_month = args.start_game_month
    start_game_day = args.start_game_day
    end_game_year = args.end_game_year
    end_game_month = args.end_game_month
    end_game_day = args.end_game_day

    start_date = dt.date(start_game_year, start_game_month, start_game_day)
    end_date = dt.date(end_game_year, end_game_month, end_game_day)

    assert start_date <= end_date, 'Start Date is after End Date. Please enter a valid date range'

    day_delta = dt.timedelta(days=1)

    print('Getting and Downloading Box Scores Between {} and {}'.format(start_date, end_date))
    while start_date <= end_date:
        """Get all box scores within the date range"""
        game_year = start_date.year
        game_month = start_date.month
        game_day = start_date.day

        player_box_scores_df = get_player_box_scores_day(
            game_year=game_year, game_month=game_month, game_day=game_day)

        start_date += day_delta


if __name__ == '__main__':
    """See https://stackoverflow.com/questions/419163/what-does-if-name-main-do"""
    main()

