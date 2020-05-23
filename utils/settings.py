
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

# https://coolors.co/ff3f3f-ffd557-009fb7-cbf257-f49a50-99627c
# https://coolors.co/8e1313-1dce84-1b772f-5542ac-298e6b-c60877
COLORS = [
    "#FF3F3F",
    "#FFD557",
    "#009FB7",
    "#CBF257",
    "#F49A50",
    "#99627C",
    "#8E1313",
    "#1DCE84",
    "#1B772F",
    "#5542AC",
    "#298E6B",
    "#C60877"
]

AGGREGATION_LEVELS_COLOR_DISCRETE_MAP = dict(
    zip(
        AGGREGATION_LEVEL_NAMES,
        COLORS
    )
)

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

AGG_LEVEL_COL = 'agg_level'
AGG_LEVEL_ID_COL = 'agg_level_id'

WRMSSE_COL = 'wrmsse'
RMSSE_COL = 'rmsse'
SALES_USD_COL = 'sales_usd'

COL_HEIGHT = 1500 # px