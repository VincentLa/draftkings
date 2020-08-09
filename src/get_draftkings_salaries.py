"""
Script to grab DraftKings Salaries

To run, cd into the root level directory of this repo. For example, run:

python -m src.get_draftkings_salaries --start_game_year=2019 --start_game_month=10 --start_game_day=22 --end_game_year=2020 --end_game_month=8 --end_game_day=7

To run a single day, set the start and end dates to be the same
"""
import argparse
import datetime as dt
import os
from pathlib import Path
from random import randint
import re
import requests
import sys
import time

import basketball_reference_web_scraper
from basketball_reference_web_scraper import client
from bs4 import BeautifulSoup
import git
import pandas as pd
from urllib.request import urlopen

import src.util as ut


GIT_ROOT_DIR = ut.get_git_root(os.path.dirname(__file__))
DATA_DIR = os.path.join(GIT_ROOT_DIR, 'data')

SECONDS_SLEEP = 2

HELP_TEXT = """
This is a runner to get DraftKings Salaries Data.

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


def normalize_position(position):
    """
    Add full roster positions
    
    For example, if PG, then the player is also a G, if PF, a player is also an F. 
    All players are UTIL
    """
    position_normalized = position.split('/')
    position_normalized = list(filter(None, position_normalized))  # Remove empty strings
    
    if 'PG' in position_normalized or 'SG' in position_normalized:
        position_normalized.append('G')
    if 'SF' in position_normalized or 'PF' in position_normalized:
        position_normalized.append('F')
    position_normalized.append('UTIL')
    position_normalized = list(set(position_normalized))
    position_normalized.sort()
    
    position_normalized = '/'.join(position_normalized)
    
    return position_normalized


def get_fantasy_salary(game_year, game_month, game_day):
    """
    Scraping DraftKings salary data from RotoGuru.com
    """
    url_roto = "http://rotoguru1.com/cgi-bin/hyday.pl?mon={}&day={}&year={}&game=dk".format(game_month, game_day, game_year)
    print('Scraping salary information for date {}-{}-{}'.format(game_year, str(game_month).rjust(2, '0'), str(game_day).rjust(2, '0')))

    teams, positions, players, starters, salaries = [], [], [], [], []

    soup = BeautifulSoup(urlopen(url_roto),'lxml')

    #Check if there were any games on a given date
    soup_table = soup.find('body').find('table', border="0", cellspacing="5")

    soup_rows = soup_table.find_all('tr')

    for row in soup_rows:
        if row.find('td').has_attr('colspan') == False:
            if row.find('a').get_text() != '':

                position = row.find_all('td')[0].get_text()
                position = normalize_position(position)

                player_tmp = row.find('a').get_text().split(", ")
                player = player_tmp[1] + ' ' + player_tmp[0]

                starter_tmp = row.find_all('td')[1].get_text()

                if '^' in starter_tmp:
                    starter = True
                else:
                    starter = False

                salary_tmp = row.find_all('td')[3].get_text()
                salary = re.sub('[$,]', '', salary_tmp)

                team = row.find_all('td')[4].get_text()

                positions.append(position)
                players.append(player)
                starters.append(starter)
                salaries.append(salary)
                teams.append(team)

    df = pd.DataFrame({'date': [dt.date(game_year, game_month, game_day) for i in range(len(players))], 
                       'team': [team.upper() for team in teams],
                       'position': positions,
                       'name': players,
                       'starter': starters,
                       'salary': salaries})

    filename = os.path.join(
        DATA_DIR, 'raw', 'draftkings_salaries', 'dk_nba_salaries_classic_{}{}{}.csv'.format(
            game_year, str(game_month).rjust(2, '0'), str(game_day).rjust(2, '0')))
    df.to_csv(filename, index=False)

    time.sleep(SECONDS_SLEEP)
    return df
    

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

        df = get_fantasy_salary(
            game_year=game_year, game_month=game_month, game_day=game_day)

        start_date += day_delta


if __name__ == '__main__':
    """See https://stackoverflow.com/questions/419163/what-does-if-name-main-do"""
    main()

