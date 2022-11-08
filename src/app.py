import os
import streamlit as st
import pandas as pd
import numpy as np
import logging
logging.basicConfig(level=logging.DEBUG,
                    format=' %(asctime)s - $(levelname)s - $(message)s', filemode='w')
logger = logging.getLogger(__name__)
logger.info('-----START-----')


@st.experimental_memo
def load_data():
    player_data = pd.read_csv('./data/players.csv')
    return player_data

player_data = load_data()





if 'page' not in st.session_state:
    st.session_state['page'] == 'head_to_head'

if st.session_state['page'] == 'head_to_head':

    if player_data.index.name != 'player':
        player_data = player_data.set_index('player') 
    
    players = player_data.sample(2)
    
    player1 = players.iloc[0]
    player2 = players.iloc[1]

    player_cols = st.






if st.session_state['page'] == 'stat_filter':

    if 'stat_filters' not in st.session_state:
        st.session_state['stat_filters'] = ['pts_per_g', 'trb_per_g', 'ast_per_g']


    def add_stat_filter():
        if not st.session_state['added_stat'] == 'Add a stat...':
            st.session_state['stat_filters'] += [st.session_state['added_stat']]
            logger.info(f"added {st.session_state['added_stat']} to stat_filters")


    def remove_stat_filter(i):
        del st.session_state['stat_filters'][i]

    inputs = []

    # TODO: make this a category filter feature
    invalid_stats = ['player', 'year_min', 'year_max', 'pos', 'height',
                    'weight', 'birth_date', 'colleges', 'season', 'age', 'team_id', 'lg_id']
    available_stats = [
        c for c in player_data if c not in invalid_stats+st.session_state['stat_filters']]
    available_stats.sort()
    available_stats = ['Add a stat...'] + available_stats

    st.selectbox('Add a stat to filter:', options=available_stats,
                on_change=add_stat_filter, key='added_stat')

    n_stat_filters = len(st.session_state['stat_filters'])

    MAX_COLS = 4
    n_cols = min([MAX_COLS, n_stat_filters])
    sf_cols = st.columns(n_cols)
    df = player_data.copy()
    filter_dict = {}
    for i, feature_name in enumerate(st.session_state['stat_filters']):
        col_n = (i) % (MAX_COLS)
        with sf_cols[col_n]:
            # TODO: suggested value should be Xth %ile of the REMAINING data
            # Have to cache data though so that it only does that on the FIRST time the slider is added
            # otherwise it will change values of subsequent sliders when you refresh one slider.
            # suggested_value = df[feature_name].quantile(.90), doesnt work,
            suggested_value = player_data[feature_name].quantile(.75)
            filter_dict[feature_name] = st.number_input(
                label=f'{feature_name}:',
                min_value=float(player_data[feature_name].min()),
                max_value=float(player_data[feature_name].max()),
                value=float(suggested_value),
                step=.1
            )
            st.button(
                'Remove', key=f'delete_filter_{i}', on_click=remove_stat_filter, args=[i])

        df = df[df[feature_name] >= filter_dict[feature_name]]

    percentiles = df[st.session_state['stat_filters']].rank(axis=0, pct=True)
    df['score'] = percentiles.sum(axis=1)
    df = df.sort_values('score', ascending=False).drop('score', axis='columns')
    df = df.reset_index()

    demog_cols = ['player', 'year_min', 'year_max', 'height']
    df = df[demog_cols + list(filter_dict.keys())]

    # dummy_size = 1 / (len(df.columns))
    # dummy_cols = st.columns([dummy_size, 2-dummy_size])
    # with dummy_cols[1]:

    st.write(df)

    logger.info('-----END-----')
    print(st.session_state['stat_filters'])
