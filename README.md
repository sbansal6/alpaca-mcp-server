# Alpaca MCP Server

This is a Model Context Protocol (MCP) server for Alpaca, allowing LLMs like Claude to interact with the Alpaca's trading API. It enables trading stocks, options, checking positions, fetching market data, and managing your account - all through natural language.

## Features

- 📊 **Market Data**
  - Get real-time stock quotes and historical price data
  - Fetch option contract information and market data
  - View option chains and snapshots with Greeks
- 💵 **Account Information**
  - Check your balances, buying power, and status
  - View account history and activities
- 📈 **Position Management**
  - View current positions and their performance
  - Close positions individually or all at once
- 🛒 **Order Placement**
  - Place market and limit orders for stocks
  - Place option orders (single-leg and multi-leg)
  - Support for various order types and time-in-force
- 📋 **Order Management**
  - List, track, and cancel orders
  - Get order history and status
- ⚙️ **Market Information**
  - Check market clock and calendar
  - View corporate announcements
  - Get option contract details

## Prerequisites

- Python 3.10+
- Alpaca API keys (with options trading enabled)
- Claude for Desktop or another MCP client

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/mcp-server-alpaca-trading-api.git
   cd mcp-server-alpaca-trading-api
   ```

2. Install the required packages:
   ```bash
   pip install mcp alpaca-py python-dotenv
   ```

3. Create a `.env` file with your Alpaca API credentials:
   ```
   API_KEY_ID=your_alpaca_api_key
   API_SECRET_KEY=your_alpaca_secret_key
   ```

## Usage

### Running the server

1. Make sure you're in the project directory:
   ```bash
   cd mcp-server-alpaca-trading-api
   ```

2. If you're using a virtual environment, activate it:
   ```bash
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. Start the server using one of these methods:

   **Option 1**: Run from the project directory
   ```bash
   python alpaca_mcp_server.py
   ```

   **Option 2**: Run with full path
   ```bash
   python /path/to/mcp-server-alpaca-trading-api/alpaca_mcp_server.py
   ```

   **Option 3**: Run as a module
   ```bash
   python -m alpaca_mcp_server
   ```

The server will start and be ready to accept connections from Claude for Desktop.

### Configuring Claude for Desktop

1. Open Claude for Desktop
2. Go to Settings
3. Click on "Developer" and then "Edit Config"
4. Add the server configuration to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "alpaca": {
      "command": "python",
      "args": [
        "/path/to/mcp-server-alpaca-trading-api/alpaca_mcp_server.py"
      ],
      "env": {
        "API_KEY_ID": "your_alpaca_api_key",
        "API_SECRET_KEY": "your_alpaca_secret_key"
      }
    }
  }
}
```

5. Save and restart Claude for Desktop

### Available Tools

The server exposes the following tools:

#### Account and Position Management
- `get_account_info()` - Get account balances and status
- `get_positions()` - List all current positions in the portfolio
- `get_open_position(symbol)` - Get details for a specific position
- `close_position(symbol)` - Close a specific position
- `close_all_positions(cancel_orders)` - Close all open positions

#### Market Data
- `get_stock_quote(symbol)` - Get the latest quote for a stock
- `get_stock_bars(symbol, days)` - Get historical price bars for a stock
- `get_market_clock()` - Get current market status and times
- `get_market_calendar(start_date, end_date)` - Get market calendar for date range

#### Option Trading
- `get_option_contracts(underlying_symbol, expiration_date, ...)` - Get option contracts
- `get_option_snapshot(symbol_or_symbols, feed)` - Get option market data and Greeks
- `place_option_market_order(legs, order_class, quantity)` - Place option orders

#### Order Management
- `get_orders(status, limit)` - List orders with specified status
- `place_stock_market_order(symbol, side, quantity)` - Place a stock market order
- `place_limit_order(symbol, side, quantity, limit_price)` - Place a limit order
- `cancel_all_orders()` - Cancel all open orders

#### Corporate Actions
- `get_corporate_announcements(ca_types, start_date, end_date, ...)` - Get corporate announcements

## Example Queries

### Basic Trading
1. What’s my current account balance and buying power?
2. Show me my current positions.
3. Buy 10 shares of AAPL at market price.
4. Sell 5 shares of TSLA with a limit price of $300.
5. Cancel all open stock orders.
6. Cancel the order with ID abc123.
7. Liquidate my entire position in GOOGL.
8. Close 10% of my position in NVDA.
9. How many shares of AMZN do I currently hold?
10. Place a limit order to buy 100 shares of MSFT at $450.
11. Place a market order to sell 25 shares of META.

### Option Trading
12. Show me available option contracts for AAPL expiring next month.
13. Get the latest quote for AAPL250616C00150000.
14. Retrieve the option snapshot for SPY240628P00400000.
15. Liquidate my position in 2 contracts of QQQ calls expiring next week.
16. Place a market order to buy 1 call option on AAPL expiring next Friday.
17. What are the Greeks for TSLA240621P00500000?
18. Find all option contracts for TSLA with strike prices near $800.
19. Get all contracts for SPY expiring in June that are call options.
20. Place a bull call spread using AAPL June options.

### Market Information
21. Is the US stock market currently open?
22. What are the market open and close times today?
23. Show me the market calendar for next week.
24. Are there any corporate announcements for AAPL this week?
25. What are the next dividend announcements for SPY?
26. List earnings announcements coming tomorrow.

### Historical & Real-time Data
27. Show me AAPL’s daily price history for the last 5 trading days.
28. What was the closing price of TSLA yesterday?
29. Get the latest bar for GOOG.
30. What was the latest trade price for NVDA?
31. Show me the most recent quote for MSFT.
32. Retrieve the last 100 trades for AMD.
33. Show me intraday bars for AMZN from last Tuesday.

### Orders
34. Show me all my open and filled orders from this week.
35. What orders do I have for AAPL?
36. List all limit orders I placed in the past 3 days.
37. Filter all orders by status: filled.
38. Get me the order history for yesterday.

### Watchlists
39. Create a new watchlist called “Tech Stocks” with AAPL, MSFT, and NVDA.
40. Update my “Favorites” watchlist to include TSLA and AMZN.
41. What stocks are in my “Dividend Picks” watchlist?
42. Remove META from my “Growth Portfolio” watchlist.
43. List all my existing watchlists.

### Asset Information
44. Search for details about the asset ‘AAPL’.
45. List all tradeable US equities.
46. Show me all active crypto assets.
47. Filter all assets with status ‘active’.
48. Show me details for the stock with symbol ‘GOOGL’.

### Combined Scenarios
49. Place a market order to buy 2 AAPL call options and update my “Earnings Bets” watchlist with AAPL.
50. Get today’s market clock and show me my buying power before placing a limit buy order for TSLA at $180.

## Note

This server uses Alpaca's paper trading by default. To use real money trading, change `paper=True` to `paper=False` in the `TradingClient` initialization.

## Security Notice

This MCP server will have access to your Alpaca account and can place real trades. Always review what Claude is suggesting before approving any trades. This is especially important for option trading, which involves more complex strategies and higher risk.

## License

MIT
