# Competition rules
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