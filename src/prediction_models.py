import pandas as pd
import src.util as ut
import os

# Prediction based on most recent mean scores, defined by number of recent games. if < than that #, use all that is available
def recent_mean(df, optdate, games=5, min_date='2020-07-30'):

    dkpts_df = pd.DataFrame()
    for file in os.listdir(ut.NBA_BOX_SCORE_DIR):
        df_box = pd.read_csv(os.path.join(ut.NBA_BOX_SCORE_DIR, file))[
            ['slug', 'name', 'date_played', 'draftkings_points']]
        dkpts_df = dkpts_df.append(df_box)


    dkpts_df = dkpts_df[dkpts_df.date_played >= min_date]
    dkpts_df = dkpts_df[dkpts_df.date_played < optdate]
    temp = dkpts_df.groupby('slug')
    temp = temp.apply(lambda x: x.sort_values('date_played', ascending=False))
    temp = temp.reset_index(drop=True)
    temp = temp.groupby('name').head(games)
    temp = temp.groupby('name').mean()

    mapping_df = pd.read_csv(ut.MAPPING_TABLE_FN)
    test = df.merge(mapping_df, how='left', left_on='name', right_on='dk_name')
    test = test.merge(temp, how='left', left_on='bbr_name', right_on='name')
    test = test.rename(columns={'draftkings_points': 'EV'})
    test.EV = test.EV.fillna(0)
    return test

