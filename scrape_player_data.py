import pandas as pd
import numpy as np
import bs4
import os
import threading
from string import ascii_lowercase
import requests
from config import Config
cfg = Config()
import logging
logging.basicConfig(level = logging.DEBUG, filename = cfg.log_dir/'scrape_player_data.log', format=' %(asctime)s -  %(levelname)s -  %(message)s', filemode='w')
logging.debug('Start of program')

base_url = "https://www.basketball-reference.com/"

def downloadStats(letter):
    player_list = []
    url = base_url + 'players/' + letter + '/'
    res = requests.get(url)
    res.raise_for_status()
    soup = bs4.BeautifulSoup(res.text, 'lxml')
    player_elements = soup.select("#players > tbody > tr")

    for player_element in player_elements:
        try:
            player_info = {x.get('data-stat'): x.getText() for x in player_element}
            stats_url = player_element.select('a')[0].get('href')
            player_res = requests.get(base_url + stats_url)
            player_res.raise_for_status()
            player_soup = bs4.BeautifulSoup(player_res.text, 'lxml')
            per_game_row_element = player_soup.select('#per_game > tfoot > tr:nth-child(1)')[0]
            player_stats = {x.get('data-stat'): x.getText() for x in per_game_row_element}
            player_info.update(player_stats)

            player_list.append(player_info)
        except:
            logging.info('Error with :')
            logging.fino(player_element)
            raise
    
    player_df = pd.DataFrame(player_list)
    tmp_loc = 'subdata/player_info_'+letter+'.csv'
    player_df.to_csv(cfg.data_dir/tmp_loc, index=False)

downloadThreads = []
for l in ascii_lowercase:
    thread = threading.Thread(target = downloadStats, args = (l))
    downloadThreads.append(thread)
    thread.start()

# wait for all threads to end
for downloadThread in downloadThreads:
    downloadThread.join()

# Now Compile
full_data = []
for l in ascii_lowercase:
    try:
        tmp_loc = 'subdata/player_info_'+l+'.csv'
        full_data.append(pd.read_csv(cfg.data_dir/tmp_loc))
    except:
        logging.info(f'Error with letter {l}')

full_pd = pd.concat(full_data)
full_pd.to_csv(cfg.data_dir/'players.csv', index = False)