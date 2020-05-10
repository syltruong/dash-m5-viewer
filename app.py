import os
import pickle
import time

import dash
import pandas as pd

from utils import evaluate, explore
from utils.settings import (
    CALENDAR_FILEPATH,
    SELL_PRICES_FILEPATH,
    SALES_FILEPATH,
    CACHE_DIR,
    ACCURACY_EVALUATOR_FILE_PATH,
    SALES_EXPLORER_FILE_PATH
)


start = time.process_time()

app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server

# warmup

if not os.path.exists(ACCURACY_EVALUATOR_FILE_PATH):
    
    calendar_df = pd.read_csv(CALENDAR_FILEPATH, parse_dates=['date'])
    sell_prices_df = pd.read_csv(SELL_PRICES_FILEPATH)
    sales_df = pd.read_csv(SALES_FILEPATH)
    
    accuracy_evaluator = evaluate.AccuracyEvaluator(
        sales_df,
        sell_prices_df,
        calendar_df
        )
    
    with open(ACCURACY_EVALUATOR_FILE_PATH, 'wb') as f:
        pickle.dump(accuracy_evaluator, f)
else:
    with open(ACCURACY_EVALUATOR_FILE_PATH, 'rb') as f:
        accuracy_evaluator = pickle.load(f)

if not os.path.exists(SALES_EXPLORER_FILE_PATH):
    
    sales_df = pd.read_csv(SALES_FILEPATH)
    calendar_df = pd.read_csv(CALENDAR_FILEPATH, parse_dates=['date'])
    
    sales_explorer = explore.SalesExplorer(
        sales_df,
        calendar_df
        )
    
    with open(SALES_EXPLORER_FILE_PATH, 'wb') as f:
        pickle.dump(sales_explorer, f)
else:
    with open(SALES_EXPLORER_FILE_PATH, 'rb') as f:
        sales_explorer = pickle.load(f)

print('Prelim steps time: {}'.format(time.process_time() - start))