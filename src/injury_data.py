import datetime
import os
import re
import requests

import pandas as pd
import pdfreader
from pdfreader import SimplePDFViewer
from tabula import read_pdf, convert_into
import src.util as ut

today = datetime.datetime.today()
today = today.strftime('%Y-%m-%d')
ROOT_DIR = os.path.abspath(os.curdir)

def download_nba_injuryreports(date):
    # # given a date in %Y-%m-%d string format, will try to download the injury reports that the nba publishes at 11, 2, and 5
    # url1 = 'https://ak-static.cms.nba.com/referee/injury/Injury-Report_' + date + '_11AM.pdf'
    # url2 = 'https://ak-static.cms.nba.com/referee/injury/Injury-Report_' + date + '_02PM.pdf'
    # url3 = 'https://ak-static.cms.nba.com/referee/injury/Injury-Report_' + date + '_05PM.pdf'

    # season updated injury report for 20-21 to 1:30, 5:30, 8:30
    url1 = 'https://ak-static.cms.nba.com/referee/injury/Injury-Report_' + date + '_01PM.pdf'
    url2 = 'https://ak-static.cms.nba.com/referee/injury/Injury-Report_' + date + '_05PM.pdf'
    url3 = 'https://ak-static.cms.nba.com/referee/injury/Injury-Report_' + date + '_08PM.pdf'

    r1 = requests.get(url1, allow_redirects=True)
    r2 = requests.get(url2, allow_redirects=True)
    r3 = requests.get(url3, allow_redirects=True)

    path = ROOT_DIR + '\\data\\raw\\injury_reports'

    if (r1.status_code == 200) and (os.path.exists(path + '\\' + 'Injury-Report_' + date + '_01PM.pdf') is False):
        open(path + "\\" + 'Injury-Report_' + date + '_11AM.pdf', 'wb').write(r1.content)
    if (r2.status_code == 200) and (os.path.exists(path + '\\' + 'Injury-Report_' + date + '_05PM.pdf') is False):
        open(path + "\\" + 'Injury-Report_' + date + '_02PM.pdf', 'wb').write(r2.content)
    if (r3.status_code == 200) and (os.path.exists(path + '\\' + 'Injury-Report_' + date + '_08PM.pdf') is False):
        open(path + "\\" + 'Injury-Report_' + date + '_05PM.pdf', 'wb').write(r3.content)

# converts pdf injury reports into csv files
def parse_injuryreports():
    path = ROOT_DIR + '\\data\\raw\\injury_reports'
    for file in os.listdir(path):
        if (os.path.exists(ROOT_DIR + '\\data\\processed\\injury_reports' + "\\" + file[:-3] + "csv") is False):
            df = read_pdf(
                path + "\\" + file,
                pages='all', stream=True, area=[49.99375, 13.15625, 563.61375, 832.00125])
            final_report = pd.DataFrame()
            for i in range(0, len(df)):
                page = pd.DataFrame(df[i])
                final_report = final_report.append(page)

            final_report.to_csv(ROOT_DIR + '\\data\\processed\\injury_reports' + "\\" + file[:-3] + "csv")

# remove players from df in on injury report - based on current status
def remove_injured_players(df, date):
    dt = datetime.datetime.strptime(date, '%Y%m%d').strftime('%Y-%m-%d')
    if os.path.exists(ROOT_DIR + '\\data\\processed\\injury_reports' + "\\" + "Injury-Report_" + dt + "_05PM.csv"):
        inj_df = pd.read_csv(
            ROOT_DIR + '\\data\\processed\\injury_reports' + "\\" + "Injury-Report_" + dt + "_05PM.csv")
    elif os.path.exists(ROOT_DIR + '\\data\\processed\\injury_reports' + "\\" + "Injury-Report_" + dt + "_02PM.csv"):
        inj_df = pd.read_csv(
            ROOT_DIR + '\\data\\processed\\injury_reports' + "\\" + "Injury-Report_" + dt + "_02PM.csv")
    else:
        inj_df = pd.read_csv(
            ROOT_DIR + '\\data\\processed\\injury_reports' + "\\" + "Injury-Report_" + dt + "_11AM.csv")

    inj_df['Game Date'] = inj_df['Game Date'].ffill()
    inj_df['Team'] = inj_df['Team'].ffill()
    inj_df = inj_df[['Game Date', 'Team', 'Player Name', 'Current Status']]
    inj_df = inj_df[inj_df['Current Status'].isin(['Out','Doubtful'])]
    inj_df = inj_df[inj_df['Game Date'] == datetime.datetime.strptime(date, '%Y%m%d').strftime('%m/%d/%Y')]
    inj_df['Player Name'] = [" ".join(n.split(", ")[::-1]) for n in inj_df['Player Name']]
    df = df[~df.name.isin(inj_df['Player Name'])]
    return df

download_nba_injuryreports(today)
parse_injuryreports()
