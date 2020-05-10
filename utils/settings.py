
import os

#
# Data paths
#

DATA_DIR = os.path.join(os.getcwd(), 'data')
CACHE_DIR = os.path.join(DATA_DIR, '.cache')
CALENDAR_FILEPATH = os.path.join(DATA_DIR, 'calendar.csv')
SELL_PRICES_FILEPATH = os.path.join(DATA_DIR, 'sell_prices.csv')
SALES_FILEPATH = os.path.join(DATA_DIR, 'sales_train_validation.csv')
ACCURACY_EVALUATOR_FILE_PATH = os.path.join(CACHE_DIR, 'accuracy_evaluator.pckl')
SALES_EXPLORER_FILE_PATH = os.path.join(CACHE_DIR, 'sales_explorer.pckl')

#
# Competition rules
#

AGGREGATION_LEVELS = [
    ("all",),
    ("state_id",),
    ("store_id",),
    ("cat_id",),
    ("dept_id",),
    ("state_id", "cat_id"),
    ("state_id", "dept_id"),
    ("store_id", "cat_id"),
    ("store_id", "dept_id"),
    ("item_id",),
    ("state_id", "item_id"),
    ("id",)
]

AGGREGATION_LEVEL_NAMES = [
    ':'.join(agg_level) for agg_level in AGGREGATION_LEVELS
]

N_VALIDATION_DAYS = 28

#
# App settings
#

AGG_FUNCTIONS =[
    'sum',
    'mean',
    'std',
    'min',
    'max',
]
