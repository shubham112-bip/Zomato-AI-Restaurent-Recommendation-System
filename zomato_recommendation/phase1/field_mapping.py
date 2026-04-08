"""
Hugging Face dataset: ManikaSaini/zomato-restaurant-recommendation

Column names match the dataset schema on the Hub (see dataset viewer / datasets.load_dataset).
If the upstream schema changes, update this module only, then adjust normalize.py if needed.
"""

# --- Raw Hugging Face column names (exact strings) ---

HF_NAME = "name"
HF_LOCATION = "location"
HF_LISTED_IN_CITY = "listed_in(city)"
HF_LISTED_IN_TYPE = "listed_in(type)"
HF_RATE = "rate"
HF_VOTES = "votes"
HF_CUISINES = "cuisines"
HF_APPROX_COST = "approx_cost(for two people)"
HF_REVIEWS_LIST = "reviews_list"
HF_MENU_ITEM = "menu_item"
HF_DISH_LIKED = "dish_liked"
HF_REST_TYPE = "rest_type"
HF_ADDRESS = "address"
HF_URL = "url"

# All columns we read from HF for normalization (subset of full dataset)
HF_COLUMNS_USED = (
    HF_NAME,
    HF_LOCATION,
    HF_LISTED_IN_CITY,
    HF_LISTED_IN_TYPE,
    HF_RATE,
    HF_VOTES,
    HF_CUISINES,
    HF_APPROX_COST,
    HF_REVIEWS_LIST,
    HF_MENU_ITEM,
    HF_DISH_LIKED,
    HF_REST_TYPE,
    HF_ADDRESS,
)

# --- Canonical internal columns (architecture §4.2) ---

COL_ID = "id"
COL_NAME = "name"
COL_CITY = "city"
COL_LOCATION = "location"
COL_CUISINES = "cuisines"
COL_RATING = "rating"
COL_COST_FOR_TWO = "cost_for_two"
COL_RAW_FEATURES = "raw_features"
COL_VOTES = "votes"
COL_SOURCE_INDEX = "source_index"

CANONICAL_COLUMNS = (
    COL_ID,
    COL_NAME,
    COL_CITY,
    COL_LOCATION,
    COL_CUISINES,
    COL_RATING,
    COL_COST_FOR_TWO,
    COL_RAW_FEATURES,
    COL_VOTES,
    COL_SOURCE_INDEX,
)

DATASET_NAME = "ManikaSaini/zomato-restaurant-recommendation"
DEFAULT_SPLIT = "train"
