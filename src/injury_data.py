import requests
import re
import datetime
import pandas as pd
import os

today = datetime.datetime.today()
today = today.strftime('%Y-%m-%d')


def download_nba_injuryreports(date):
    # given a date in %Y-%m-%d string format, will try to download the injury reports that the nba publishes at 11, 2, and 5
    url1 = 'https://ak-static.cms.nba.com/referee/injury/Injury-Report_' + date + '_11AM.pdf'
    url2 = 'https://ak-static.cms.nba.com/referee/injury/Injury-Report_' + date + '_02PM.pdf'
    url3 = 'https://ak-static.cms.nba.com/referee/injury/Injury-Report_' + date + '_05PM.pdf'
    r1 = requests.get(url1, allow_redirects=True)
    r2 = requests.get(url2, allow_redirects=True)
    r3 = requests.get(url3, allow_redirects=True)

    os.chdir('C:\\Users\\Kevin\\Documents\\GitHub\\draftkings\\data\\raw\\injury_reports')
    if r1.status_code == 200:
        open('Injury-Report_' + date + '_11AM.pdf', 'wb').write(r1.content)
    if r2.status_code == 200:
        open('Injury-Report_' + date + '_02PM.pdf', 'wb').write(r2.content)
    if r3.status_code == 200:
        open('Injury-Report_' + date + '_05PM.pdf', 'wb').write(r3.content)

# download_nba_injuryreports(today)

