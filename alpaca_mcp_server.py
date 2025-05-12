import os
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta, date
from mcp.server.fastmcp import FastMCP
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetOrdersRequest, MarketOrderRequest, LimitOrderRequest, GetAssetsRequest, CreateWatchlistRequest, UpdateWatchlistRequest, GetCalendarRequest, GetCorporateAnnouncementsRequest, ClosePositionRequest, GetOptionContractsRequest, OptionLegRequest
from alpaca.trading.enums import OrderSide, TimeInForce, QueryOrderStatus, AssetStatus, CorporateActionType, CorporateActionDateType, OrderType, PositionIntent, ContractType, OrderClass
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.historical.option import OptionHistoricalDataClient
from alpaca.data.requests import Sort, StockBarsRequest, StockLatestQuoteRequest, StockTradesRequest, StockLatestTradeRequest, StockLatestBarRequest, OptionLatestQuoteRequest, OptionSnapshotRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.live.stock import StockDataStream
from alpaca.trading.models import Order
from alpaca.data.enums import DataFeed, OptionsFeed
from alpaca.common.enums import SupportedCurrencies

import time

# Please do not change these variables
trade_api_url = None
trade_api_wss = None
data_api_url = None
stream_data_wss = None

# Initialize FastMCP server
mcp = FastMCP("alpaca-trading")

# Initialize Alpaca clients using environment variables
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv("API_KEY_ID")
API_SECRET = os.getenv("API_SECRET_KEY")

# Check if keys are available
if not API_KEY or not API_SECRET:
    raise ValueError("Alpaca API credentials not found in environment variables.")

# Initialize clients
# For trading
trade_client = TradingClient(API_KEY, API_SECRET, paper=True)
# For historical market data
stock_historical_data_client = StockHistoricalDataClient(API_KEY, API_SECRET)
# For streaming market data
stock_data_stream_client = StockDataStream(API_KEY, API_SECRET, url_override = stream_data_wss)
# For option historical data
option_historical_data_client = OptionHistoricalDataClient(api_key=API_KEY, secret_key=API_SECRET)

# ============================================================================
# Account Information Tools
# ============================================================================

@mcp.tool()
async def get_account_info() -> str:
    """
    Retrieves and formats the current account information including balances and status.
    
    Returns:
        str: Formatted string containing account details including:
            - Account ID
            - Status
            - Currency
            - Buying Power
            - Cash Balance
            - Portfolio Value
            - Equity
            - Market Values
            - Pattern Day Trader Status
            - Day Trades Remaining
    """
    account = trade_client.get_account()
    
    info = f"""
            Account Information:
            -------------------
            Account ID: {account.id}
            Status: {account.status}
            Currency: {account.currency}
            Buying Power: ${float(account.buying_power):.2f}
            Cash: ${float(account.cash):.2f}
            Portfolio Value: ${float(account.portfolio_value):.2f}
            Equity: ${float(account.equity):.2f}
            Long Market Value: ${float(account.long_market_value):.2f}
            Short Market Value: ${float(account.short_market_value):.2f}
            Pattern Day Trader: {'Yes' if account.pattern_day_trader else 'No'}
            Day Trades Remaining: {account.daytrade_count if hasattr(account, 'daytrade_count') else 'Unknown'}
            """
    return info

@mcp.tool()
async def get_positions() -> str:
    """
    Retrieves and formats all current positions in the portfolio.
    
    Returns:
        str: Formatted string containing details of all open positions including:
            - Symbol
            - Quantity
            - Market Value
            - Average Entry Price
            - Current Price
            - Unrealized P/L
    """
    positions = trade_client.get_all_positions()
    
    if not positions:
        return "No open positions found."
    
    result = "Current Positions:\n-------------------\n"
    for position in positions:
        result += f"""
                    Symbol: {position.symbol}
                    Quantity: {position.qty} shares
                    Market Value: ${float(position.market_value):.2f}
                    Average Entry Price: ${float(position.avg_entry_price):.2f}
                    Current Price: ${float(position.current_price):.2f}
                    Unrealized P/L: ${float(position.unrealized_pl):.2f} ({float(position.unrealized_plpc) * 100:.2f}%)
                    -------------------
                    """
    return result

@mcp.tool()
async def get_open_position(symbol: str) -> str:
    """
    Retrieves and formats details for a specific open position.
    
    Args:
        symbol (str): The symbol name of the asset to get position for (e.g., 'AAPL', 'MSFT')
    
    Returns:
        str: Formatted string containing the position details or an error message
    """
    try:
        position = trade_client.get_open_position(symbol)
        return f"""
                Position Details for {symbol}:
                ---------------------------
                Quantity: {position.qty} shares
                Market Value: ${float(position.market_value):.2f}
                Average Entry Price: ${float(position.avg_entry_price):.2f}
                Current Price: ${float(position.current_price):.2f}
                Unrealized P/L: ${float(position.unrealized_pl):.2f}
                """ 
    except Exception as e:
        return f"Error fetching position: {str(e)}"

# ============================================================================
# Market Data Tools
# ============================================================================

@mcp.tool()
async def get_stock_quote(symbol: str) -> str:
    """
    Retrieves and formats the latest quote for a stock.
    
    Args:
        symbol (str): Stock ticker symbol (e.g., AAPL, MSFT)
    
    Returns:
        str: Formatted string containing:
            - Ask Price
            - Bid Price
            - Ask Size
            - Bid Size
            - Timestamp
    """
    try:
        request_params = StockLatestQuoteRequest(symbol_or_symbols=symbol)
        quotes = stock_historical_data_client.get_stock_latest_quote(request_params)
        
        if symbol in quotes:
            quote = quotes[symbol]
            return f"""
                    Latest Quote for {symbol}:
                    ------------------------
                    Ask Price: ${quote.ask_price:.2f}
                    Bid Price: ${quote.bid_price:.2f}
                    Ask Size: {quote.ask_size}
                    Bid Size: {quote.bid_size}
                    Timestamp: {quote.timestamp}
                    """ 
        else:
            return f"No quote data found for {symbol}."
    except Exception as e:
        return f"Error fetching quote for {symbol}: {str(e)}"

@mcp.tool()
async def get_stock_bars(symbol: str, days: int = 5) -> str:
    """
    Retrieves and formats historical price bars for a stock.
    
    Args:
        symbol (str): Stock ticker symbol (e.g., AAPL, MSFT)
        days (int): Number of trading days to look back (default: 5)
    
    Returns:
        str: Formatted string containing historical price data including:
            - Date
            - Open
            - High
            - Low
            - Close
            - Volume
    """
    try:
        # Calculate start time based on days
        start_time = datetime.now().date() - timedelta(days=days)
        
        request_params = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=TimeFrame.Day,
            start=start_time
        )
        
        bars = stock_historical_data_client.get_stock_bars(request_params)
        
        # if symbol in bars and bars[symbol]:
        if bars[symbol]:
            result = f"Historical Data for {symbol} (Last {days} trading days):\n"
            result += "---------------------------------------------------\n"
            
            for bar in bars[symbol]:
                result += f"Date: {bar.timestamp.date()}, Open: ${bar.open:.2f}, High: ${bar.high:.2f}, Low: ${bar.low:.2f}, Close: ${bar.close:.2f}, Volume: {bar.volume}\n"
            
            return result
        else:
            return f"No historical data found for {symbol} in the last {days} days."
    except Exception as e:
        return f"Error fetching historical data for {symbol}: {str(e)}"

@mcp.tool()
async def get_stock_trades(
    symbol: str,
    days: int = 5,
    limit: Optional[int] = None,
    sort: Optional[Sort] = Sort.ASC,
    feed: Optional[DataFeed] = None,
    currency: Optional[SupportedCurrencies] = None,
    asof: Optional[str] = None
) -> str:
    """
    Retrieves and formats historical trades for a stock.
    
    Args:
        symbol (str): Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        days (int): Number of days to look back (default: 5)
        limit (Optional[int]): Upper limit of number of data points to return
        sort (Optional[Sort]): Chronological order of response (ASC or DESC)
        feed (Optional[DataFeed]): The stock data feed to retrieve from
        currency (Optional[SupportedCurrencies]): Currency for prices (default: USD)
        asof (Optional[str]): The asof date in YYYY-MM-DD format
    
    Returns:
        str: Formatted string containing trade history or an error message
    """
    try:
        # Calculate start time based on days
        start_time = datetime.now() - timedelta(days=days)
        
        # Create the request object with all available parameters
        request_params = StockTradesRequest(
            symbol_or_symbols=symbol,
            start=start_time,
            end=datetime.now(),
            limit=limit,
            sort=sort,
            feed=feed,
            currency=currency,
            asof=asof
        )
        
        # Get the trades
        trades = stock_historical_data_client.get_stock_trades(request_params)
        
        if symbol in trades:
            result = f"Historical Trades for {symbol} (Last {days} days):\n"
            result += "---------------------------------------------------\n"
            
            for trade in trades[symbol]:
                result += f"""
                    Time: {trade.timestamp}
                    Price: ${float(trade.price):.2f}
                    Size: {trade.size}
                    Exchange: {trade.exchange}
                    ID: {trade.id}
                    Conditions: {trade.conditions}
                    -------------------
                    """
            return result
        else:
            return f"No trade data found for {symbol} in the last {days} days."
    except Exception as e:
        return f"Error fetching trades: {str(e)}"

@mcp.tool()
async def get_stock_latest_trade(
    symbol: str,
    feed: Optional[DataFeed] = None,
    currency: Optional[SupportedCurrencies] = None
) -> str:
    """Get the latest trade for a stock.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        feed: The stock data feed to retrieve from (optional)
        currency: The currency for prices (optional, defaults to USD)
    
    Returns:
        A formatted string containing the latest trade details or an error message
    """
    try:
        # Create the request object with all available parameters
        request_params = StockLatestTradeRequest(
            symbol_or_symbols=symbol,
            feed=feed,
            currency=currency
        )
        
        # Get the latest trade
        latest_trades = stock_historical_data_client.get_stock_latest_trade(request_params)
        
        if symbol in latest_trades:
            trade = latest_trades[symbol]
            return f"""
                Latest Trade for {symbol}:
                ---------------------------
                Time: {trade.timestamp}
                Price: ${float(trade.price):.2f}
                Size: {trade.size}
                Exchange: {trade.exchange}
                ID: {trade.id}
                Conditions: {trade.conditions}
                """
        else:
            return f"No latest trade data found for {symbol}."
    except Exception as e:
        return f"Error fetching latest trade: {str(e)}"

@mcp.tool()
async def get_stock_latest_bar(
    symbol: str,
    feed: Optional[DataFeed] = None,
    currency: Optional[SupportedCurrencies] = None
) -> str:
    """Get the latest minute bar for a stock.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        feed: The stock data feed to retrieve from (optional)
        currency: The currency for prices (optional, defaults to USD)
    
    Returns:
        A formatted string containing the latest bar details or an error message
    """
    try:
        # Create the request object with all available parameters
        request_params = StockLatestBarRequest(
            symbol_or_symbols=symbol,
            feed=feed,
            currency=currency
        )
        
        # Get the latest bar
        latest_bars = stock_historical_data_client.get_stock_latest_bar(request_params)
        
        if symbol in latest_bars:
            bar = latest_bars[symbol]
            return f"""
                Latest Minute Bar for {symbol}:
                ---------------------------
                Time: {bar.timestamp}
                Open: ${float(bar.open):.2f}
                High: ${float(bar.high):.2f}
                Low: ${float(bar.low):.2f}
                Close: ${float(bar.close):.2f}
                Volume: {bar.volume}
                """
        else:
            return f"No latest bar data found for {symbol}."
    except Exception as e:
        return f"Error fetching latest bar: {str(e)}"

# ============================================================================
# Order Management Tools
# ============================================================================

@mcp.tool()
async def get_orders(status: str = "all", limit: int = 10) -> str:
    """
    Retrieves and formats orders with the specified status.
    
    Args:
        status (str): Order status to filter by (open, closed, all)
        limit (int): Maximum number of orders to return (default: 10)
    
    Returns:
        str: Formatted string containing order details including:
            - Symbol
            - ID
            - Type
            - Side
            - Quantity
            - Status
            - Submission Time
            - Fill Details (if applicable)
    """
    try:
        # Convert status string to enum
        if status.lower() == "open":
            query_status = QueryOrderStatus.OPEN
        elif status.lower() == "closed":
            query_status = QueryOrderStatus.CLOSED
        else:
            query_status = QueryOrderStatus.ALL
            
        request_params = GetOrdersRequest(
            status=query_status,
            limit=limit
        )
        
        orders = trade_client.get_orders(request_params)
        
        if not orders:
            return f"No {status} orders found."
        
        result = f"{status.capitalize()} Orders (Last {len(orders)}):\n"
        result += "-----------------------------------\n"
        
        for order in orders:
            result += f"""
                        Symbol: {order.symbol}
                        ID: {order.id}
                        Type: {order.type}
                        Side: {order.side}
                        Quantity: {order.qty}
                        Status: {order.status}
                        Submitted At: {order.submitted_at}
                        """
            if hasattr(order, 'filled_at') and order.filled_at:
                result += f"Filled At: {order.filled_at}\n"
                
            if hasattr(order, 'filled_avg_price') and order.filled_avg_price:
                result += f"Filled Price: ${float(order.filled_avg_price):.2f}\n"
                
            result += "-----------------------------------\n"
            
        return result
    except Exception as e:
        return f"Error fetching orders: {str(e)}"

@mcp.tool()
async def place_stock_market_order(symbol: str, side: str, quantity: float) -> str:
    """
    Places a market order and returns the order details.
    
    Args:
        symbol (str): Stock ticker symbol (e.g., AAPL, MSFT)
        side (str): Order side (buy or sell)
        quantity (float): Number of shares to buy or sell
    
    Returns:
        str: Formatted string containing order details including:
            - Order ID
            - Symbol
            - Side
            - Quantity
            - Type
            - Time In Force
            - Status
            - Client Order ID
            - Position Intent
    """
    try:
        # Convert side string to enum
        if side.lower() == "buy":
            order_side = OrderSide.BUY
        elif side.lower() == "sell":
            order_side = OrderSide.SELL
        else:
            return f"Invalid order side: {side}. Must be 'buy' or 'sell'."
        
        # Create market order request
        order_data = MarketOrderRequest(
            symbol=symbol,
            qty=quantity,
            side=order_side,
            type=OrderType.MARKET,
            time_in_force=TimeInForce.DAY,
            extended_hours=False,
            client_order_id=f"mcp_{int(time.time())}",
            position_intent=PositionIntent.BTO if order_side == OrderSide.BUY else PositionIntent.STO
        )
        
        # Submit order
        order = trade_client.submit_order(order_data)
        
        return f"""
                Market Order Placed Successfully:
                --------------------------------
                Order ID: {order.id}
                Symbol: {order.symbol}
                Side: {order.side}
                Quantity: {order.qty}
                Type: {order.type}
                Time In Force: {order.time_in_force}
                Status: {order.status}
                Client Order ID: {order.client_order_id}
                Position Intent: {order.position_intent}
                """
    except Exception as e:
        return f"Error placing order: {str(e)}"

@mcp.tool()
async def place_limit_order(
    symbol: str, 
    side: str, 
    quantity: float, 
    limit_price: float,
    extended_hours: bool = False,
    client_order_id: Optional[str] = None
) -> str:
    """
    Place a limit order.
    
    Args:
        symbol: Stock ticker symbol (e.g., AAPL, MSFT)
        side: Order side (buy or sell)
        quantity: Number of shares to buy or sell
        limit_price: Limit price for the order
        extended_hours: Whether to allow execution during extended hours (default: False)
        client_order_id: Optional custom identifier for the order
    """
    try:
        # Input validation
        if not symbol or not isinstance(symbol, str):
            return "Invalid symbol: Must be a non-empty string"
        if not isinstance(quantity, (int, float)) or quantity <= 0:
            return "Invalid quantity: Must be a positive number"
        if not isinstance(limit_price, (int, float)) or limit_price <= 0:
            return "Invalid limit price: Must be a positive number"

        # Convert side string to enum
        if side.lower() == "buy":
            order_side = OrderSide.BUY
            position_intent = PositionIntent.BTO
        elif side.lower() == "sell":
            order_side = OrderSide.SELL
            position_intent = PositionIntent.STO
        else:
            return f"Invalid order side: {side}. Must be 'buy' or 'sell'."
        
        # Create limit order request
        order_data = LimitOrderRequest(
            symbol=symbol,
            qty=quantity,
            side=order_side,
            type=OrderType.LIMIT,  # Required parameter
            time_in_force=TimeInForce.DAY,
            limit_price=limit_price,
            extended_hours=extended_hours,
            client_order_id=client_order_id or f"limit_{int(time.time())}",
            position_intent=position_intent
        )
        
        # Submit order
        order = trade_client.submit_order(order_data)
        
        return f"""
                Limit Order Placed Successfully:
                -------------------------------
                Order ID: {order.id}
                Symbol: {order.symbol}
                Side: {order.side}
                Quantity: {order.qty}
                Type: {order.type}
                Limit Price: ${float(order.limit_price):.2f}
                Time In Force: {order.time_in_force}
                Status: {order.status}
                Client Order ID: {order.client_order_id}
                Position Intent: {order.position_intent}
                Extended Hours: {order.extended_hours}
                """
    except Exception as e:
        return f"Error placing limit order: {str(e)}"

@mcp.tool()
async def cancel_all_orders() -> str:
    """
    Cancel all open orders.
    
    Returns:
        A formatted string containing the status of each cancelled order.
    """
    try:
        # Cancel all orders
        cancel_responses = trade_client.cancel_orders()
        
        if not cancel_responses:
            return "No orders were found to cancel."
        
        # Format the response
        response_parts = ["Order Cancellation Results:"]
        response_parts.append("-" * 30)
        
        for response in cancel_responses:
            status = "Success" if response.status == 200 else "Failed"
            response_parts.append(f"Order ID: {response.id}")
            response_parts.append(f"Status: {status}")
            if response.body:
                response_parts.append(f"Details: {response.body}")
            response_parts.append("-" * 30)
        
        return "\n".join(response_parts)
        
    except Exception as e:
        return f"Error cancelling orders: {str(e)}"

@mcp.tool()
async def cancel_order_by_id(order_id: str) -> str:
    """
    Cancel a specific order by its ID.
    
    Args:
        order_id: The UUID of the order to cancel
        
    Returns:
        A formatted string containing the status of the cancelled order.
    """
    try:
        # Cancel the specific order
        response = trade_client.cancel_order_by_id(order_id)
        
        # Format the response
        status = "Success" if response.status == 200 else "Failed"
        result = f"""
        Order Cancellation Result:
        ------------------------
        Order ID: {response.id}
        Status: {status}
        """
        
        if response.body:
            result += f"Details: {response.body}\n"
            
        return result
        
    except Exception as e:
        return f"Error cancelling order {order_id}: {str(e)}"

# ============================================================================
# Position Management Tools
# ============================================================================

@mcp.tool()
async def close_position(symbol: str, qty: Optional[str] = None, percentage: Optional[str] = None) -> str:
    """
    Closes a specific position for a single symbol.
    
    Args:
        symbol (str): The symbol of the position to close
        qty (Optional[str]): Optional number of shares to liquidate
        percentage (Optional[str]): Optional percentage of shares to liquidate
    
    Returns:
        str: Formatted string containing position closure details
    """
    try:
        # Create close position request if options are provided
        close_options = None
        if qty or percentage:
            close_options = ClosePositionRequest(
                qty=qty,
                percentage=percentage
            )
        
        # Close the position
        order = trade_client.close_position(symbol, close_options)
        
        return f"""
                Position Closed Successfully:
                ----------------------------
                Symbol: {symbol}
                Order ID: {order.id}
                Status: {order.status}
                """
                
    except Exception as e:
        return f"Error closing position: {str(e)}"
    
@mcp.tool()
async def close_all_positions(cancel_orders: bool = False) -> str:
    """
    Closes all open positions.
    
    Args:
        cancel_orders (bool): If True, cancels all open orders before liquidating positions
    
    Returns:
        str: Formatted string containing position closure results
    """
    try:
        # Close all positions
        close_responses = trade_client.close_all_positions(cancel_orders=cancel_orders)
        
        if not close_responses:
            return "No positions were found to close."
        
        # Format the response
        response_parts = ["Position Closure Results:"]
        response_parts.append("-" * 30)
        
        for response in close_responses:
            response_parts.append(f"Symbol: {response.symbol}")
            response_parts.append(f"Status: {response.status}")
            if response.order_id:
                response_parts.append(f"Order ID: {response.order_id}")
            response_parts.append("-" * 30)
        
        return "\n".join(response_parts)
        
    except Exception as e:
        return f"Error closing positions: {str(e)}"

# ============================================================================
# Asset Information Tools
# ============================================================================

@mcp.tool()
async def get_asset_info(symbol: str) -> str:
    """
    Retrieves and formats detailed information about a specific asset.
    
    Args:
        symbol (str): The symbol of the asset to get information for
    
    Returns:
        str: Formatted string containing asset details including:
            - Name
            - Exchange
            - Class
            - Status
            - Trading Properties
    """
    try:
        asset = trade_client.get_asset(symbol)
        return f"""
                Asset Information for {symbol}:
                ----------------------------
                Name: {asset.name}
                Exchange: {asset.exchange}
                Class: {asset.asset_class}
                Status: {asset.status}
                Tradable: {'Yes' if asset.tradable else 'No'}
                Marginable: {'Yes' if asset.marginable else 'No'}
                Shortable: {'Yes' if asset.shortable else 'No'}
                Easy to Borrow: {'Yes' if asset.easy_to_borrow else 'No'}
                Fractionable: {'Yes' if asset.fractionable else 'No'}
                """
    except Exception as e:
        return f"Error fetching asset information: {str(e)}"

@mcp.tool()
async def get_all_assets(
    status: Optional[str] = None,
    asset_class: Optional[str] = None,
    exchange: Optional[str] = None,
    attributes: Optional[str] = None
) -> str:
    """
    Get all available assets with optional filtering.
    
    Args:
        status: Filter by asset status (e.g., 'active', 'inactive')
        asset_class: Filter by asset class (e.g., 'us_equity', 'crypto')
        exchange: Filter by exchange (e.g., 'NYSE', 'NASDAQ')
        attributes: Comma-separated values to query for multiple attributes
    """
    try:
        # Create filter if any parameters are provided
        filter_params = None
        if any([status, asset_class, exchange, attributes]):
            filter_params = GetAssetsRequest(
                status=status,
                asset_class=asset_class,
                exchange=exchange,
                attributes=attributes
            )
        
        # Get all assets
        assets = trade_client.get_all_assets(filter_params)
        
        if not assets:
            return "No assets found matching the criteria."
        
        # Format the response
        response_parts = ["Available Assets:"]
        response_parts.append("-" * 30)
        
        for asset in assets:
            response_parts.append(f"Symbol: {asset.symbol}")
            response_parts.append(f"Name: {asset.name}")
            response_parts.append(f"Exchange: {asset.exchange}")
            response_parts.append(f"Class: {asset.asset_class}")
            response_parts.append(f"Status: {asset.status}")
            response_parts.append(f"Tradable: {'Yes' if asset.tradable else 'No'}")
            response_parts.append("-" * 30)
        
        return "\n".join(response_parts)
        
    except Exception as e:
        return f"Error fetching assets: {str(e)}"

# ============================================================================
# Watchlist Management Tools
# ============================================================================

@mcp.tool()
async def create_watchlist(name: str, symbols: List[str]) -> str:
    """
    Creates a new watchlist with specified symbols.
    
    Args:
        name (str): Name of the watchlist
        symbols (List[str]): List of symbols to include in the watchlist
    
    Returns:
        str: Confirmation message with watchlist creation status
    """
    try:
        watchlist_data = CreateWatchlistRequest(name=name, symbols=symbols)
        watchlist = trade_client.create_watchlist(watchlist_data)
        return f"Watchlist '{name}' created successfully with {len(symbols)} symbols."
    except Exception as e:
        return f"Error creating watchlist: {str(e)}"

@mcp.tool()
async def get_watchlists() -> str:
    """Get all watchlists for the account."""
    try:
        watchlists = trade_client.get_watchlists()
        result = "Watchlists:\n------------\n"
        for wl in watchlists:
            result += f"Name: {wl.name}\n"
            result += f"ID: {wl.id}\n"
            result += f"Created: {wl.created_at}\n"
            result += f"Updated: {wl.updated_at}\n"
            result += f"Symbols: {', '.join(wl.assets)}\n\n"
        return result
    except Exception as e:
        return f"Error fetching watchlists: {str(e)}"

@mcp.tool()
async def update_watchlist(watchlist_id: str, name: str = None, symbols: List[str] = None) -> str:
    """Update an existing watchlist."""
    try:
        update_request = UpdateWatchlistRequest(name=name, symbols=symbols)
        watchlist = trade_client.update_watchlist_by_id(watchlist_id, update_request)
        return f"Watchlist updated successfully: {watchlist.name}"
    except Exception as e:
        return f"Error updating watchlist: {str(e)}"

# ============================================================================
# Market Information Tools
# ============================================================================

@mcp.tool()
async def get_market_clock() -> str:
    """
    Retrieves and formats current market status and next open/close times.
    
    Returns:
        str: Formatted string containing:
            - Current Time
            - Market Open Status
            - Next Open Time
            - Next Close Time
    """
    try:
        clock = trade_client.get_clock()
        return f"""
Market Status:
-------------
Current Time: {clock.timestamp}
Is Open: {'Yes' if clock.is_open else 'No'}
Next Open: {clock.next_open}
Next Close: {clock.next_close}
"""
    except Exception as e:
        return f"Error fetching market clock: {str(e)}"

@mcp.tool()
async def get_market_calendar(start_date: str, end_date: str) -> str:
    """
    Retrieves and formats market calendar for specified date range.
    
    Args:
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
    
    Returns:
        str: Formatted string containing market calendar information
    """
    try:
        calendar = trade_client.get_calendar(start=start_date, end=end_date)
        result = f"Market Calendar ({start_date} to {end_date}):\n----------------------------\n"
        for day in calendar:
            result += f"Date: {day.date}, Open: {day.open}, Close: {day.close}\n"
        return result
    except Exception as e:
        return f"Error fetching market calendar: {str(e)}"

# ============================================================================
# Corporate Actions Tools
# ============================================================================

@mcp.tool()
async def get_corporate_announcements(
    ca_types: List[CorporateActionType],
    since: date,
    until: date,
    symbol: Optional[str] = None,
    cusip: Optional[str] = None,
    date_type: Optional[CorporateActionDateType] = None
) -> str:
    """
    Retrieves and formats corporate action announcements.
    
    Args:
        ca_types (List[CorporateActionType]): List of corporate action types to filter by
        since (date): Start date for the announcements
        until (date): End date for the announcements
        symbol (Optional[str]): Optional stock symbol to filter by
        cusip (Optional[str]): Optional CUSIP to filter by
        date_type (Optional[CorporateActionDateType]): Optional date type to filter by
    
    Returns:
        str: Formatted string containing corporate announcement details
    """
    try:
        request = GetCorporateAnnouncementsRequest(
            ca_types=ca_types,
            since=since,
            until=until,
            symbol=symbol,
            cusip=cusip,
            date_type=date_type
        )
        announcements = trade_client.get_corporate_announcements(request)
        result = "Corporate Announcements:\n----------------------\n"
        for ann in announcements:
            result += f"""
                        ID: {ann.id}
                        Corporate Action ID: {ann.corporate_action_id}
                        Type: {ann.ca_type}
                        Sub Type: {ann.ca_sub_type}
                        Initiating Symbol: {ann.initiating_symbol}
                        Target Symbol: {ann.target_symbol}
                        Declaration Date: {ann.declaration_date}
                        Ex Date: {ann.ex_date}
                        Record Date: {ann.record_date}
                        Payable Date: {ann.payable_date}
                        Cash: {ann.cash}
                        Old Rate: {ann.old_rate}
                        New Rate: {ann.new_rate}
                        ----------------------
                        """
        return result
    except Exception as e:
        return f"Error fetching corporate announcements: {str(e)}"

# ============================================================================
# Options Trading Tools
# ============================================================================

@mcp.tool()
async def get_option_contracts(
    underlying_symbol: str,
    expiration_date: Optional[date] = None,
    strike_price_gte: Optional[str] = None,
    strike_price_lte: Optional[str] = None,
    type: Optional[ContractType] = None,
    status: Optional[AssetStatus] = None,
    root_symbol: Optional[str] = None,
    limit: Optional[int] = None
) -> str:
    """
    Retrieves and formats option contracts based on specified criteria.
    
    Args:
        underlying_symbol (str): The symbol of the underlying asset
        expiration_date (Optional[date]): Optional expiration date for the options
        strike_price_gte (Optional[str]): Optional minimum strike price
        strike_price_lte (Optional[str]): Optional maximum strike price
        type (Optional[ContractType]): Optional contract type (CALL or PUT)
        status (Optional[AssetStatus]): Optional asset status filter (e.g., ACTIVE)
        root_symbol (Optional[str]): Optional root symbol for the option
        limit (Optional[int]): Optional maximum number of contracts to return
    
    Returns:
        str: Formatted string containing option contracts information
    """
    try:
        # Create the request object with all available parameters
        request = GetOptionContractsRequest(
            underlying_symbols=[underlying_symbol],
            expiration_date=expiration_date,
            strike_price_gte=strike_price_gte,
            strike_price_lte=strike_price_lte,
            type=type,
            status=status,
            root_symbol=root_symbol,
            limit=limit
        )
        
        # Get the option contracts
        contracts = trade_client.get_option_contracts(request)
        
        if not contracts:
            return f"No option contracts found for {underlying_symbol} matching the criteria."
        
        # Format the response
        result = f"Option Contracts for {underlying_symbol}:\n"
        result += "----------------------------------------\n"
        
        for contract in contracts:
            result += f"""
                Symbol: {contract.symbol}
                Type: {contract.type}
                Strike Price: ${float(contract.strike_price):.2f}
                Expiration Date: {contract.expiration_date}
                Status: {contract.status}
                Root Symbol: {contract.root_symbol}
                Underlying Symbol: {contract.underlying_symbol}
                Exercise Style: {contract.exercise_style}
                -------------------------
                """
        
        return result
        
    except Exception as e:
        return f"Error fetching option contracts: {str(e)}"

@mcp.tool()
async def get_option_latest_quote(
    symbol: str,
    feed: Optional[OptionsFeed] = None
) -> str:
    """
    Retrieves and formats the latest quote for an option contract.
    
    Args:
        symbol (str): The option contract symbol (e.g., 'O:AAPL230616C00150000')
        feed (Optional[OptionsFeed]): The source feed of the data (opra or indicative).
            Default: opra if the user has the options subscription, indicative otherwise.
    
    Returns:
        str: Formatted string containing the latest quote information including:
            - Ask Price
            - Bid Price
            - Ask Size
            - Bid Size
            - Timestamp
    """
    try:
        # Create the request object
        request = OptionLatestQuoteRequest(
            symbol_or_symbols=symbol,
            feed=feed
        )
        
        # Get the latest quote
        quotes = option_historical_data_client.get_option_latest_quote(request)
        
        if symbol in quotes:
            quote = quotes[symbol]
            return f"""
                Latest Quote for {symbol}:
                ------------------------
                Ask Price: ${float(quote.ask_price):.2f}
                Bid Price: ${float(quote.bid_price):.2f}
                Ask Size: {quote.ask_size}
                Bid Size: {quote.bid_size}
                Timestamp: {quote.timestamp}
                """
        else:
            return f"No quote data found for {symbol}."
            
    except Exception as e:
        return f"Error fetching option quote: {str(e)}"

@mcp.tool()
async def place_option_market_order(
    legs: List[Dict[str, Any]],
    order_class: Optional[OrderClass] = None,
    quantity: int = 1
) -> str:
    """
    Places a market order for options (single or multi-leg) and returns the order details.
    
    Args:
        legs (List[Dict[str, Any]]): List of option legs, where each leg is a dictionary containing:
            - symbol (str): Option contract symbol (e.g., 'AAPL230616C00150000')
            - side (str): 'buy' or 'sell'
            - ratio_qty (int): Quantity ratio for the leg
        order_class (Optional[OrderClass]): Order class (SIMPLE, BRACKET, OCO, OTO, MLEG)
            Defaults to SIMPLE for single leg, MLEG for multi-leg
        quantity (int): Base quantity for the order (default: 1)
    
    Returns:
        str: Formatted string containing order details
    """
    try:
        # Validate legs
        if not legs:
            return "Error: No option legs provided"
        
        # Validate quantity
        if quantity <= 0:
            return "Error: Quantity must be positive"
        
        # Determine order class if not provided
        if order_class is None:
            order_class = OrderClass.MLEG if len(legs) > 1 else OrderClass.SIMPLE
        
        # Convert legs to OptionLegRequest objects
        order_legs = []
        for leg in legs:
            # Validate ratio_qty
            if not isinstance(leg['ratio_qty'], int) or leg['ratio_qty'] <= 0:
                return f"Error: Invalid ratio_qty for leg {leg['symbol']}. Must be positive integer."
            
            # Convert side string to enum
            if leg['side'].lower() == "buy":
                order_side = OrderSide.BUY
            elif leg['side'].lower() == "sell":
                order_side = OrderSide.SELL
            else:
                return f"Invalid order side: {leg['side']}. Must be 'buy' or 'sell'."
            
            order_legs.append(OptionLegRequest(
                symbol=leg['symbol'],
                side=order_side,
                ratio_qty=leg['ratio_qty']
            ))
        
        # Determine position intent based on the first leg for single-leg orders
        # For multi-leg orders, we'll use BTO as default since it's a spread
        position_intent = PositionIntent.BTO if order_legs[0].side == OrderSide.BUY else PositionIntent.STO
        
        # Create market order request
        order_data = MarketOrderRequest(
            qty=quantity,
            order_class=order_class,
            time_in_force=TimeInForce.DAY,
            client_order_id=f"mcp_opt_{int(time.time())}",
            position_intent=position_intent,
            type=OrderType.MARKET  # Explicitly set order type
        )
        
        # Add legs only for multi-leg orders
        if order_class == OrderClass.MLEG:
            order_data.legs = order_legs
        else:
            # For single-leg orders, use the first leg's symbol
            order_data.symbol = order_legs[0].symbol
        
        # Submit order
        order = trade_client.submit_order(order_data)
        
        # Format the response
        result = f"""
                Option Market Order Placed Successfully:
                --------------------------------------
                Order ID: {order.id}
                Order Class: {order.order_class}
                Time In Force: {order.time_in_force}
                Status: {order.status}
                Client Order ID: {order.client_order_id}
                Quantity: {order.qty}
                Position Intent: {order.position_intent}
                Type: {order.type}
                """
        
        if order_class == OrderClass.MLEG:
            result += "\nLegs:\n"
            for leg in order.legs:
                result += f"""
                        Symbol: {leg.symbol}
                        Side: {leg.side}
                        Ratio Quantity: {leg.ratio_qty}
                        -------------------------
                        """
        else:
            result += f"""
                    Symbol: {order.symbol}
                    Side: {order_legs[0].side}
                    -------------------------
                    """
        
        return result
        
    except Exception as e:
        return f"Error placing option order: {str(e)}"

@mcp.tool()
async def get_option_snapshot(symbol_or_symbols: Union[str, List[str]], feed: Optional[OptionsFeed] = None) -> str:
    """
    Retrieves snapshots of option contracts including latest trade, quote, implied volatility, and Greeks.
    
    Args:
        symbol_or_symbols (Union[str, List[str]]): Single option symbol or list of option symbols
        feed (Optional[OptionsFeed]): The source feed of the data (opra or indicative).
            Default: opra if the user has the options subscription, indicative otherwise.
    
    Returns:
        str: Formatted string containing snapshot information including:
            - Latest Quote (bid/ask prices, sizes, exchanges, conditions, tape)
            - Latest Trade (price, size, exchange, conditions, tape)
            - Implied Volatility
            - Greeks (delta, gamma, rho, theta, vega)
    """
    try:
        # Create snapshot request
        request = OptionSnapshotRequest(
            symbol_or_symbols=symbol_or_symbols,
            feed=feed
        )
        
        # Get snapshots
        snapshots = option_historical_data_client.get_option_snapshot(request)
        
        # Format the response
        result = "Option Snapshots:\n"
        result += "================\n\n"
        
        # Handle both single symbol and list of symbols
        symbols = [symbol_or_symbols] if isinstance(symbol_or_symbols, str) else symbol_or_symbols
        
        for symbol in symbols:
            snapshot = snapshots.get(symbol)
            if snapshot is None:
                result += f"No data available for {symbol}\n"
                continue
                
            result += f"Symbol: {symbol}\n"
            result += "-----------------\n"
            
            # Latest Quote
            if snapshot.latest_quote:
                quote = snapshot.latest_quote
                result += f"Latest Quote:\n"
                result += f"  Bid Price: ${quote.bid_price:.2f}\n"
                result += f"  Ask Price: ${quote.ask_price:.2f}\n"
                result += f"  Bid Size: {quote.bid_size}\n"
                result += f"  Ask Size: {quote.ask_size}\n"
                if quote.bid_exchange:
                    result += f"  Bid Exchange: {quote.bid_exchange}\n"
                if quote.ask_exchange:
                    result += f"  Ask Exchange: {quote.ask_exchange}\n"
                if quote.conditions:
                    result += f"  Conditions: {quote.conditions}\n"
                if quote.tape:
                    result += f"  Tape: {quote.tape}\n"
                result += f"  Timestamp: {quote.timestamp.strftime('%Y-%m-%d %H:%M:%S %Z')}\n"
            
            # Latest Trade
            if snapshot.latest_trade:
                trade = snapshot.latest_trade
                result += f"Latest Trade:\n"
                result += f"  Price: ${trade.price:.2f}\n"
                result += f"  Size: {trade.size}\n"
                if trade.exchange:
                    result += f"  Exchange: {trade.exchange}\n"
                if trade.conditions:
                    result += f"  Conditions: {trade.conditions}\n"
                if trade.tape:
                    result += f"  Tape: {trade.tape}\n"
                if trade.id:
                    result += f"  Trade ID: {trade.id}\n"
                result += f"  Timestamp: {trade.timestamp.strftime('%Y-%m-%d %H:%M:%S %Z')}\n"
            
            # Implied Volatility
            if snapshot.implied_volatility is not None:
                result += f"Implied Volatility: {snapshot.implied_volatility:.2%}\n"
            
            # Greeks
            if snapshot.greeks:
                greeks = snapshot.greeks
                result += f"Greeks:\n"
                result += f"  Delta: {greeks.delta:.4f}\n"
                result += f"  Gamma: {greeks.gamma:.4f}\n"
                result += f"  Rho: {greeks.rho:.4f}\n"
                result += f"  Theta: {greeks.theta:.4f}\n"
                result += f"  Vega: {greeks.vega:.4f}\n"
            
            result += "\n"
        
        return result
        
    except Exception as e:
        return f"Error retrieving option snapshots: {str(e)}"

# Run the server
if __name__ == "__main__":
    mcp.run(transport='stdio')