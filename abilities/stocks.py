import asyncio
import yfinance as yf

from datetime import datetime, timedelta
from typing import Type
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from collections.abc import (
    Callable,
)
from typing import (
    Any,
    TypeVar,
)
_T = TypeVar("_T")

def async_func_wrapper(target, *args: Any):
    loop = asyncio.new_event_loop()
    results = loop.run_until_complete(target(*args))
    loop.close()
    return results

def async_add_executor_job(
    # loop: asyncio.AbstractEventLoop,
    target: Callable[..., _T],
    *args: Any,
) -> asyncio.Future[_T]:
    """Add an executor job from within the event loop."""
    # task = loop.run_in_executor(None, target, *args)
    task = asyncio.get_running_loop().run_in_executor(None, async_func_wrapper, target, *args)
    return task

async def get_current_stock_price(ticker):
    """Method to get current stock price"""

    ticker_data = yf.Ticker(ticker)
    recent = ticker_data.history(period="1d")
    return {"price": recent.iloc[0]["Close"], "currency": "USD"}


async def get_stock_performance(ticker, days):
    """Method to get stock price change in percentage"""

    past_date = datetime.today() - timedelta(days=days)
    ticker_data = yf.Ticker(ticker)
    history = ticker_data.history(start=past_date)
    old_price = history.iloc[0]["Close"]
    current_price = history.iloc[-1]["Close"]
    return {"percent_change": ((current_price - old_price) / old_price) * 100}


class CurrentStockPriceInput(BaseModel):
    ticker: str = Field(description="Ticker symbol of the stock")


class CurrentStockPriceTool(BaseTool):
    name = "get_current_stock_price"
    description = """
        Useful when you want to get current stock price.
        You should enter the stock ticker symbol recognized by the yahoo finance
        """
    args_schema: Type[BaseModel] = CurrentStockPriceInput

    def _run(self, ticker: str):
        raise NotImplementedError("Synchronous execution is not supported for this tool.")

    async def _arun(self, ticker: str):
        loop = asyncio.get_running_loop()
        return await async_add_executor_job(get_current_stock_price, ticker)


class StockPercentChangeInput(BaseModel):
    ticker: str = Field(description="Ticker symbol of the stock")
    days: int = Field(description="Timedelta days to get past date from current date")


class StockPerformanceTool(BaseTool):
    name = "get_stock_performance"
    description = """
        Useful when you want to check performance of the stock.
        You should enter the stock ticker symbol recognized by the yahoo finance.
        You should enter days as number of days from today from which performance needs to be check.
        output will be the change in the stock price represented as a percentage.
        """
    args_schema: Type[BaseModel] = StockPercentChangeInput

    def _run(self, ticker: str, days: int):
        raise NotImplementedError("Synchronous execution is not supported for this tool.")

    async def _arun(self, ticker: str, days: int):
        loop = asyncio.get_running_loop()
        tasks = set()
        return await async_add_executor_job(loop, tasks, get_stock_performance, ticker, days)
