import datetime
import os
import re
import requests

import pandas as pd
import pdfreader
from pdfreader import SimplePDFViewer
from tabula import read_pdf, convert_into

today = datetime.datetime.today()
today = today.strftime('%Y-%m-%d')
ROOT_DIR = os.path.abspath(os.curdir)

def download_nba_injuryreports(date):
    # given a date in %Y-%m-%d string format, will try to download the injury reports that the nba publishes at 11, 2, and 5
    url1 = 'https://ak-static.cms.nba.com/referee/injury/Injury-Report_' + date + '_11AM.pdf'
    url2 = 'https://ak-static.cms.nba.com/referee/injury/Injury-Report_' + date + '_02PM.pdf'
    url3 = 'https://ak-static.cms.nba.com/referee/injury/Injury-Report_' + date + '_05PM.pdf'
    r1 = requests.get(url1, allow_redirects=True)
    r2 = requests.get(url2, allow_redirects=True)
    r3 = requests.get(url3, allow_redirects=True)

    path = ROOT_DIR + '\\data\\raw\\injury_reports'

    if (r1.status_code == 200) and (os.path.exists(path + '\\' + 'Injury-Report_' + date + '_11AM.pdf') is False):
        open(path + "\\" + 'Injury-Report_' + date + '_11AM.pdf', 'wb').write(r1.content)
    if (r2.status_code == 200) and (os.path.exists(path + '\\' + 'Injury-Report_' + date + '_02PM.pdf') is False):
        open(path + "\\" + 'Injury-Report_' + date + '_02PM.pdf', 'wb').write(r2.content)
    if (r3.status_code == 200) and (os.path.exists(path + '\\' + 'Injury-Report_' + date + '_05PM.pdf') is False):
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


download_nba_injuryreports(today)
parse_injuryreports()