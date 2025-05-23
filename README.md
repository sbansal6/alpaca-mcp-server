# Alpaca MCP Server

This is a Model Context Protocol (MCP) server implementation for Alpaca's Trading API. It enables large language models (LLMs) like Claude Desktop, Cursor, or VScode to interact with Alpaca's trading infrastructure using natural language. This server supports stock trading, options trading, portfolio management, watchlist handling, and real-time market data access.

## Features

- **Market Data**
  - Real-time quotes, trades, and price bars for stocks
  - Historical OHLCV data and trade history
  - Option contract quotes and Greeks (via snapshots)
- **Account Management**
  - View balances, buying power, and account status
  - Inspect all open and closed positions
- **Position Management**
  - Get detailed info on individual holdings
  - Liquidate all or partial positions by share count or percentage
- **Order Management**
  - Place stock and option orders (market or limit)
  - Cancel orders individually or in bulk
  - Retrieve full order history
- **Options Trading**
  - Search and retrieve option contracts by expiration or strike
  - Place multi-leg options strategies
  - Get latest quotes and Greeks for contracts
- **Market Status & Corporate Actions**
  - Check if markets are open
  - Fetch market calendar and trading sessions
  - View upcoming corporate announcements (earnings, splits, dividends)
- **Watchlist Management**
  - Create, update, and view personal watchlists
  - Manage multiple watchlists for tracking assets
- **Asset Search**
  - Query details for stocks and other Alpaca-supported assets

## Prerequisites

- Python 3.10+
- Alpaca API keys (with paper or live trading access)
- Claude for Desktop or another compatible MCP client

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/mcp-server-alpaca-trading-api.git
   cd mcp-server-alpaca-trading-api
   ```

2. Install the required packages:

   ```bash
   pip install mcp alpaca-py python-dotenv
   ```

3. Add a `.env` file for your credentials:

   ```
   API_KEY_ID=your_alpaca_api_key
   API_SECRET_KEY=your_alpaca_secret_key
   ```

## Usage

### Start the MCP Server

From the project directory:

```bash
python alpaca_mcp_server.py
```

Or use a module invocation:

```bash
python -m alpaca_mcp_server
```

### Claude for Desktop Configuration

1. Open Claude Desktop
2. Navigate to: `Settings → Developer → Edit Config`
3. Update your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "alpaca": {
      "command": "python",
      "args": [
        "/path/to/alpaca_mcp_server.py"
      ],
      "env": {
        "API_KEY_ID": "your_alpaca_api_key",
        "API_SECRET_KEY": "your_alpaca_secret_key"
      }
    }
  }
}
```

## Available Tools

### Account & Positions

* `get_account_info()` – View balance, margin, and account status
* `get_positions()` – List all held assets
* `get_open_position(symbol)` – Detailed info on a specific position
* `close_position(symbol, qty|percentage)` – Close part or all of a position
* `close_all_positions(cancel_orders)` – Liquidate entire portfolio

### Stock Market Data

* `get_stock_quote(symbol)` – Real-time bid/ask quote
* `get_stock_bars(symbol, start_date, end_date)` – OHLCV historical bars
* `get_stock_latest_trade(symbol)` – Latest market trade price
* `get_stock_latest_bar(symbol)` – Most recent OHLC bar
* `get_stock_trades(symbol, start_time, end_time)` – Trade-level history

### Orders

* `get_orders(status, limit)` – Retrieve all or filtered orders
* `place_stock_market_order(symbol, side, quantity)` – Buy/sell at market
* `place_limit_order(symbol, side, quantity, limit_price)` – Submit limit order
* `cancel_order_by_id(order_id)` – Cancel a specific order
* `cancel_all_orders()` – Cancel all open orders

### Options

* `get_option_contracts(underlying_symbol, expiration_date)` – Fetch contracts
* `get_option_latest_quote(option_symbol)` – Latest bid/ask on contract
* `get_option_snapshot(symbol_or_symbols)` – Get Greeks and underlying
* `place_option_market_order(legs, order_class, quantity)` – Execute option strategy

### Market Info & Corporate Actions

* `get_market_clock()` – Market open/close schedule
* `get_market_calendar(start, end)` – Holidays and trading days
* `get_corporate_announcements(...)` – Earnings, dividends, splits

### Watchlists

* `create_watchlist(name, symbols)` – Create a new list
* `update_watchlist(id, name, symbols)` – Modify an existing list
* `get_watchlists()` – Retrieve all saved watchlists

### Assets

* `get_asset_info(symbol)` – Search asset metadata
* `get_all_assets(status)` – List all tradable instruments

## Example Natural Language Queries

See the “Example Queries” section below for 50 real examples covering everything from trading to corporate data to option strategies.

Thank you for the correction. Based on that, here is the fully updated **`## Note`** section of your `README.md` reflecting:

* That **you must set the keys in both `secret.py` and the Claude for Desktop config**
* That **live trading is enabled by changing the `paper=False` flag**

---

## Note

This MCP server connects to Alpaca’s **paper trading API** by default for safe testing.
To enable **live trading with real funds**, update the following configuration files:

### 🔐 Set Your API Credentials in Two Places:

1. **Claude for Desktop Configuration**

   In `claude_desktop_config.json`, provide your keys for your live account as environment variables:

   ```json
   {
     "mcpServers": {
       "alpaca": {
         "command": "python",
         "args": [
           "/path/to/alpaca_mcp_server.py"
         ],
         "env": {
           "API_KEY_ID": "your_alpaca_api_key",
           "API_SECRET_KEY": "your_alpaca_secret_key"
         }
       }
     }
   }
   ```

2. **`secret.py` in the project directory**

   ```python
   API_KEY = "your_alpaca_api_key"
   API_SECRET = "your_alpaca_secret_key"
   ```

## ⚠️ Security Notice

This server can place real trades and access your portfolio. Treat your API keys as sensitive credentials. Review all actions proposed by the LLM carefully, especially for complex options strategies or multi-leg trades.

## License

MIT
