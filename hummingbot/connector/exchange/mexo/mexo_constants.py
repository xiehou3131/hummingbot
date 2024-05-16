from hummingbot.core.api_throttler.data_types import LinkedLimitWeightPair, RateLimit
from hummingbot.core.data_type.in_flight_order import OrderState

DEFAULT_DOMAIN = "io"

HBOT_ORDER_ID_PREFIX = "hummingbot"
MAX_ORDER_ID_LEN = 32

# Base URL
REST_URL = "https://api.mexo.{}/openapi/"
WSS_URL = "wss://wsapi.mexo.{}/openapi/quote/ws/v1"
USER_DATA_STREAM_URL = "wss://wsapi.mexo.{}/openapi/ws"

PUBLIC_API_VERSION = "v1"
PRIVATE_API_VERSION = "v1"

# Public API endpoints or MexoClient function
TICKER_PRICE_CHANGE_PATH_URL = "quote/v1/ticker/24hr"
EXCHANGE_INFO_PATH_URL = "/brokerInfo"
PING_PATH_URL = "/ping"
SNAPSHOT_PATH_URL = "quote/v1/depth"
SERVER_TIME_PATH_URL = "/time"

# Private API endpoints or MexoClient function
ACCOUNTS_PATH_URL = "/account"
MY_TRADES_PATH_URL = "/myTrades"
ORDER_PATH_URL = "/order"
MEXO_USER_STREAM_PATH_URL = "/userDataStream"

WS_HEARTBEAT_TIME_INTERVAL = 1

# Mexo params

SIDE_BUY = 'BUY'
SIDE_SELL = 'SELL'

TIME_IN_FORCE_GTC = 'GTC'  # Good till cancelled
TIME_IN_FORCE_IOC = 'IOC'  # Immediate or cancel
TIME_IN_FORCE_FOK = 'FOK'  # Fill or kill

# Rate Limit Type
REQUEST_WEIGHT = "REQUEST_WEIGHT"
ORDERS = "ORDERS"

# Rate Limit time intervals
ONE_MINUTE = 60
ONE_SECOND = 1
ONE_DAY = 86400

MAX_REQUEST = 5000

# Order States
ORDER_STATE = {
    "PENDING": OrderState.PENDING_CREATE,
    "NEW": OrderState.OPEN,
    "FILLED": OrderState.FILLED,
    "PARTIALLY_FILLED": OrderState.PARTIALLY_FILLED,
    "PENDING_CANCEL": OrderState.OPEN,
    "CANCELED": OrderState.CANCELED,
    "REJECTED": OrderState.FAILED,
    "EXPIRED": OrderState.FAILED,
}

# Websocket topic types
# DIFF_EVENT_TYPE = "depthUpdate"
# TRADE_EVENT_TYPE = "trade"
DIFF_TOPIC_TYPE = "diffDepth"
TRADE_TOPIC_TYPE = "trade"

RATE_LIMITS = [
    # Pools
    RateLimit(limit_id=REQUEST_WEIGHT, limit=3000, time_interval=ONE_MINUTE),
    RateLimit(limit_id=ORDERS, limit=60, time_interval=ONE_MINUTE),
    # Weighted Limits
    RateLimit(limit_id=TICKER_PRICE_CHANGE_PATH_URL, limit=MAX_REQUEST, time_interval=ONE_MINUTE,
              linked_limits=[LinkedLimitWeightPair(REQUEST_WEIGHT, 40)]),
    RateLimit(limit_id=EXCHANGE_INFO_PATH_URL, limit=MAX_REQUEST, time_interval=ONE_MINUTE,
              linked_limits=[(LinkedLimitWeightPair(REQUEST_WEIGHT, 10))]),
    RateLimit(limit_id=SNAPSHOT_PATH_URL, limit=MAX_REQUEST, time_interval=ONE_MINUTE,
              linked_limits=[LinkedLimitWeightPair(REQUEST_WEIGHT, 50)]),
    RateLimit(limit_id=MEXO_USER_STREAM_PATH_URL, limit=MAX_REQUEST, time_interval=ONE_MINUTE,
              linked_limits=[LinkedLimitWeightPair(REQUEST_WEIGHT, 1)]),
    RateLimit(limit_id=SERVER_TIME_PATH_URL, limit=MAX_REQUEST, time_interval=ONE_MINUTE,
              linked_limits=[LinkedLimitWeightPair(REQUEST_WEIGHT, 1)]),
    RateLimit(limit_id=PING_PATH_URL, limit=MAX_REQUEST, time_interval=ONE_MINUTE,
              linked_limits=[LinkedLimitWeightPair(REQUEST_WEIGHT, 1)]),
    RateLimit(limit_id=ACCOUNTS_PATH_URL, limit=MAX_REQUEST, time_interval=ONE_MINUTE,
              linked_limits=[LinkedLimitWeightPair(REQUEST_WEIGHT, 10)]),
    RateLimit(limit_id=MY_TRADES_PATH_URL, limit=MAX_REQUEST, time_interval=ONE_MINUTE,
              linked_limits=[LinkedLimitWeightPair(REQUEST_WEIGHT, 10)]),
    RateLimit(limit_id=ORDER_PATH_URL, limit=MAX_REQUEST, time_interval=ONE_MINUTE,
              linked_limits=[LinkedLimitWeightPair(REQUEST_WEIGHT, 1),
                             LinkedLimitWeightPair(ORDERS, 1)]),
]

ORDER_NOT_EXIST_ERROR_CODE = -2013
ORDER_NOT_EXIST_MESSAGE = "Order does not exist"
UNKNOWN_ORDER_ERROR_CODE = -2011
UNKNOWN_ORDER_MESSAGE = "Unknown order sent"
