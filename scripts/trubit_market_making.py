import os
import time
import random
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Set

from pydantic import Field, validator

from hummingbot.client.config.config_data_types import ClientFieldData
from hummingbot.connector.connector_base import ConnectorBase
from hummingbot.core.clock import Clock
from hummingbot.core.data_type.common import OrderType, PositionMode, PriceType, TradeType
from hummingbot.data_feed.candles_feed.candles_factory import CandlesConfig
from hummingbot.smart_components.executors.position_executor.data_types import (
    PositionExecutorConfig,
    TripleBarrierConfig,
)
from hummingbot.smart_components.models.executor_actions import CreateExecutorAction, StopExecutorAction
from hummingbot.strategy.strategy_v2_base import StrategyV2Base, StrategyV2ConfigBase

class StrategyState(Enum):
    Paused = 1
    Opening = 2
    Error = 3


class PMMWithPositionExecutorConfig(StrategyV2ConfigBase):
    script_file_name: str = Field(default_factory=lambda: os.path.basename(__file__))
    candles_config: List[CandlesConfig] = []
    controllers_config: List[str] = []
    markets: Dict[str, Set[str]] = {}

    price_feeder_connector_name: str = Field(
        default="binance",
        client_data=ClientFieldData(
            prompt_on_new=True,
            prompt=lambda mi: "Enter the price feeder connector name:",
        )
    )

    market_maker_connector_name: str = Field(
        default="binance_perpetual_testnet",
        client_data=ClientFieldData(
            prompt_on_new=True,
            prompt=lambda mi: "Enter the market maker connector name:",
        )
    )

    trading_pair: str = Field(
        default="CFX-USDT",
        client_data=ClientFieldData(
            prompt_on_new=True,
            prompt=lambda mi: "Enter the trading_pair:",
        )
    )

    leverage: int = Field(
        default=1, gt=0,
        client_data=ClientFieldData(
            prompt_on_new=True,
            prompt=lambda mi: "Enter the leverage (e.g. 20): "
        )
    )

    order_amount_base: Decimal = Field(
        default=30, gt=0,
        client_data=ClientFieldData(
            prompt=lambda mi: "Enter the amount of base asset to be used per order (e.g. 30): ",
            prompt_on_new=True))
    
    executor_refresh_time: int = Field(
        default=20, gt=0,
        client_data=ClientFieldData(
            prompt=lambda mi: "Enter the time in seconds to refresh the executor (e.g. 20): ",
            prompt_on_new=True))
    
    spread: Decimal = Field(
        default=Decimal("0.0001"), gt=0,
        client_data=ClientFieldData(
            prompt=lambda mi: "Enter the spread (e.g. 0.003): ",
            prompt_on_new=True))
    
    level: Decimal = Field(
        default=Decimal("5"), gt=1,
        client_data=ClientFieldData(
            prompt=lambda mi: "Enter the level (e.g. 5): ",
            prompt_on_new=True))
    
    # position_mode: PositionMode = Field(
    #     default="HEDGE",
    #     client_data=ClientFieldData(
    #         prompt=lambda mi: "Enter the position mode (HEDGE/ONEWAY): ",
    #         prompt_on_new=True
    #     )
    # )

    @property
    def triple_barrier_config(self) -> TripleBarrierConfig:
        return TripleBarrierConfig(
            open_order_type=OrderType.LIMIT,
        )

    # # @validator('position_mode', pre=True, allow_reuse=True)
    # # def validate_position_mode(cls, v: str) -> PositionMode:
    #     if v.upper() in PositionMode.__members__:
    #         return PositionMode[v.upper()]
    #     raise ValueError(f"Invalid position mode: {v}. Valid options are: {', '.join(PositionMode.__members__)}")
 

class PMMSingleLevel(StrategyV2Base):
    test = 0

    @classmethod
    def get_trading_pair_for_connector(cls, token, connector):
        return "CFX-USDT"

    @classmethod
    def init_markets(cls, config: PMMWithPositionExecutorConfig):
        markets = {
            config.price_feeder_connector_name: {config.trading_pair},
            config.market_maker_connector_name: {config.trading_pair}
        }
        cls.markets = markets

    def __init__(self, connectors: Dict[str, ConnectorBase], config: PMMWithPositionExecutorConfig):
        super().__init__(connectors, config)
        self.config = config  # Only for type checking

        self._strategy_state = StrategyState.Opening
        self._last_trade_timestamp = 0

    def start(self, clock: Clock, timestamp: float) -> None:
        """
        Start the strategy.
        :param clock: Clock to use.
        :param timestamp: Current time.
        """
        self._last_timestamp = timestamp
        self.apply_initial_setting()

    def create_actions_proposal(self) -> List[CreateExecutorAction]:
        """
        Create actions proposal based on the current state of the executors.
        """
        create_actions = []

        if self._strategy_state == StrategyState.Opening:
            mid_price = self.connectors[self.config.price_feeder_connector_name].get_mid_price(self.config.trading_pair)
            up_price = Decimal(int((mid_price + Decimal("0.0001")) * Decimal("10000")) / 10000)
            down_price = Decimal(int(mid_price * Decimal("10000")) / 10000)
            order_price = random.choice([up_price, down_price])

            create_actions.append(CreateExecutorAction(
                    executor_config=PositionExecutorConfig(
                        timestamp=self.current_timestamp,
                        trading_pair=self.config.trading_pair,
                        connector_name=self.config.market_maker_connector_name,
                        side=TradeType.BUY,
                        amount=self.config.order_amount_base,
                        entry_price=order_price,
                        triple_barrier_config=self.config.triple_barrier_config,
                        leverage=self.config.leverage
                    )
                ))
            
            create_actions.append(CreateExecutorAction(
                    executor_config=PositionExecutorConfig(
                        timestamp=self.current_timestamp,
                        trading_pair=self.config.trading_pair,
                        connector_name=self.config.market_maker_connector_name,
                        side=TradeType.SELL,
                        amount=self.config.order_amount_base,
                        entry_price=order_price,
                        triple_barrier_config=self.config.triple_barrier_config,
                        leverage=self.config.leverage
                    )
                ))
            # TODO: maker orders make a trade

            self._last_trade_timestamp = int(time.time())

            for i in range(int(self.config.level)):
                entry_price_buy = down_price - Decimal(i) * self.config.spread

                create_actions.append(CreateExecutorAction(
                    executor_config=PositionExecutorConfig(
                        timestamp=self.current_timestamp,
                        trading_pair=self.config.trading_pair,
                        connector_name=self.config.market_maker_connector_name,
                        side=TradeType.BUY,
                        amount=self.config.order_amount_base,
                        entry_price=entry_price_buy,
                        triple_barrier_config=self.config.triple_barrier_config,
                        leverage=self.config.leverage
                    )
                ))

                entry_price_sell = up_price + Decimal(i) * self.config.spread

                create_actions.append(CreateExecutorAction(
                    executor_config=PositionExecutorConfig(
                        timestamp=self.current_timestamp,
                        trading_pair=self.config.trading_pair,
                        connector_name=self.config.market_maker_connector_name,
                        side=TradeType.SELL,
                        amount=self.config.order_amount_base,
                        entry_price=entry_price_sell,
                        triple_barrier_config=self.config.triple_barrier_config,
                        leverage=self.config.leverage
                    )
                ))


            self._strategy_state = StrategyState.Paused


        return create_actions

    def stop_actions_proposal(self) -> List[StopExecutorAction]:
        """
        Create a list of actions to stop the executors based on order refresh and early stop conditions.
        """
        stop_actions = []

        if self._strategy_state == StrategyState.Paused and self._last_trade_timestamp + self.config.executor_refresh_time >= int(time.time()):

            executors = self.get_all_executors()
            stop_actions.extend(self.filter_executors(
                executors=executors,
                filter_func=lambda x: not x.is_trading and x.is_active
            ))

            
            self._strategy_state = StrategyState.Opening
        return stop_actions


    def apply_initial_setting(self):
        pass
        # for connector_name, connector in self.connectors.items():
        #     if self.is_perpetual(connector_name):
        #         connector.set_position_mode(self.config.position_mode)
        #         for trading_pair in self.market_data_provider.get_trading_pairs(connector_name):
        #             connector.set_leverage(trading_pair, self.config.leverage)
