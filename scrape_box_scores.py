#%%
from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy as np
import threading
from config import Config
cfg = Config()
import threading
from functools import reduce
import logging
logging.basicConfig(level = logging.DEBUG, filename = cfg.log_dir/'scrape_box_scores.log', format=' %(asctime)s -  %(levelname)s -  %(message)s', filemode='w')
logging.debug('Start of Program')

start_year = 2000
end_year = 2021

base_url = 'https://www.basketball-reerence.com'

# First, get all game ids

def one_month_game_ids(year, month):
    res = requests.get('https://www.basketball-reference.com/leagues/NBA_' + str(year) + '_games-' + month + '.html')
    res.raise_for_status()
    soup = BeautifulSoup(res.text, 'lxml')
    game_elements = soup.find_all('th', {'class': 'left', 'data-stat':'date_game'})
    return [game.get('csk') for game in game_elements]

# Now, get the box scores

def one_box_score(game_id):
    res = requests.get('https://www.basketball-reference.com/boxscores/' + game_id + '.html')
    res.raise_for_status()
    soup = BeautifulSoup(res.text, 'lxml')
    game_time = soup.find('div', {'class': 'scorebox_meta'}).find('div').text
    tables = pd.read_html(res.text, header = 1, na_values = ['Did Not Play', 'Not With Team', 'Did Not Dress'])
    # Currently, the tables are in the following order:
    # Home: Basic Game, Q1, Q2, H1, Q3, Q4, H2, Advanced Game
    # and then the same for away
    # so we only want 0, 7, 8, 15
    #basic_stats = [tables[i] for ]
    tables = [tables[i] for i in [0, 7, 8, 15]]

    cleaned_tables = []
    for table in tables:
        # We want to tag all starters as starters and reserves as reserves
        table.rename({'Starters': 'Player'}, axis = 'columns', inplace = True)
        reserve_idx = table.index[table['Player'] == 'Reserves']
        starter_col = np.concatenate([np.repeat('Starter', reserve_idx), np.repeat('Reserve', table.shape[0] - reserve_idx)])
        table['Starter'] = starter_col
        table = table.drop(index = table.index[table['Player'].isin(['Reserves', 'Team Totals'])])
        table = table[~table['MP'].isna()]
        cleaned_tables.append(table)

    basic_stats = pd.concat((cleaned_tables[0], cleaned_tables[2]))
    advanced_stats = pd.concat((cleaned_tables[1], cleaned_tables[3]))
    box_score = basic_stats.merge(advanced_stats, on = ['Player', 'MP', 'Starter'])

    box_score.columns = [c.replace('%', '_Percentage') for c in box_score.columns]
    box_score.columns = [c.replace('+/-', 'PlusMinus') for c in box_score.columns]
    box_score['MP'] = [int(t.split(':')[0]) + int(t.split(':')[1]) / 60 for t in box_score['MP']]

    for col in [c for c in box_score.columns if c not in ['Player', 'Starter']]:
        box_score[col] = pd.to_numeric(box_score[col])

    box_score['GameID'] = game_id
    box_score['DateTime'] = pd.to_datetime(game_time)
    return box_score

def pull_one_month(year, month):
    logging.info('Game IDs for: ' + str(year) + ' ' + str(month))
    try:
        ids = one_month_game_ids(year, month)
        month_scores = []
        for id in ids:
            month_scores.append(one_box_score(id))
        out_data = pd.concat(month_scores)
        tmp_loc = 'subdata/BoxScores_' + str(year) + str(month) + '.csv'
        out_data.to_csv(cfg.data_dir/tmp_loc, index = False)
    except:
        logging.info('Error pulling game ids for' + str(year)+str(month))

    

#%%
months = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']
years = range(start_year, end_year)

downloadThreads = []
for year in years:
    for month in months:
        thread = threading.Thread(target = pull_one_month, args = (year, month))
        downloadThreads.append(thread)
        thread.start()

for downloadThread in downloadThreads:
    downloadThread.join()

full_data = []
for year in years:
    for month in months:
        try:
            tmp_loc = 'subdata/BoxScores_' + str(year) + str(month) + '.csv'
            tmp_data = pd.read_csv(cfg.data_dir/tmp_loc)
        except:
            tmp_data = pd.DataFrame()
        full_data.append(tmp_data)
full_data = pd.concat(full_data)
full_data.to_csv(cfg.data_dir/'AllBoxScores.csv', index = False)

# #%%
# all_box_scores = []
# counter = 0
# for id in game_ids[6:]:
#     success = False
#     tries = 0
#     if counter % 1000 == 0:
#         print('Pulled' + str(counter) + ' box scores. ' + str(np.round(counter / len(game_ids), 2)) + r'% done')
#     all_box_scores.append(one_box_score(id))
#     counter += 1
#     print(counter)
#     # while (not success) & (tries < 2):
#     #     try:
#     #         all_box_scores.append(one_box_score(id))
#     #         print('pulled')
#     #         success = True
#     #         counter += 1
#     #     except:
#     #         tries += 1
#     #         logging.debug('Error with ' + str(id) + '. Sleeping then trying again')
    #         time.sleep(5)

# %%
