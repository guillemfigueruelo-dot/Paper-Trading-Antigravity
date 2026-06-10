# Handoff Report: Python Trading Bot Implementation Strategy

## 1. Observation
- The Python Bot must be built in the `/bot` directory and have an entry point `main.py` or `bot.py` with a `--dry-run` CLI argument.
- It must connect to Finnhub for market data (prices, recent data) for the following assets: XAU/USD, AAPL, TSLA, MSFT, GOOGL, AMZN.
- It must use the Google AI Studio (Gemini) API to return structured trade decisions (BUY, SELL, HOLD) along with a justification.
- It must connect to Supabase to calculate viable trade sizes based on available USD, update the `portfolio` table, and log history in the `trades` table.
- The `portfolio` table stores both USD balance and asset holdings under the `asset_symbol` and `balance` columns.
- The bot must support concurrent processing for multiple assets.
- Dependencies include `supabase-py` and `google-genai` (or `google-generativeai`).

## 2. Logic Chain
1. **File Structure**: A modular approach is needed. Separating clients (Finnhub, Gemini, Supabase) from the core trading logic ensures maintainability and easier unit testing. A main orchestrator handles CLI flags and concurrency.
2. **API Patterns**:
   - *Finnhub*: Need a client to fetch current quotes (`/quote`) and recent context (e.g., news or basic moving averages) to feed into Gemini.
   - *Gemini*: Structured outputs should be strictly enforced using Pydantic models with the Gemini API to guarantee the output is parseable as `{"action": "BUY|SELL|HOLD", "justification": "..."}`.
   - *Supabase*: The `supabase-py` client will fetch the USD balance to calculate max buying power and asset balances to calculate max selling power.
3. **Order Calculation Logic**: 
   - A deterministic order sizing strategy should be used to avoid exhausting the USD balance on a single asset. For a `BUY`, allocating a fixed percentage (e.g., 10%) of the total available USD per trade, converted to asset quantity via current price. For a `SELL`, liquidating 100% of the current holding is a safe initial strategy.
4. **Concurrency**: Python's `asyncio` or `concurrent.futures.ThreadPoolExecutor` can be used to analyze assets and fetch data simultaneously, speeding up the decision phase. Execution of DB updates should be synchronized or handled carefully to avoid race conditions on the USD balance.

## 3. Caveats
- **Finnhub Symbol Compatibility**: Forex/Commodity pairs like `XAU/USD` might have different symbol formats in Finnhub (e.g., `OANDA:XAU_USD` or `BINANCE:XAUUSDT`). The bot must map logical symbols to Finnhub-specific symbols.
- **Database Transactions**: `supabase-py` does not natively support multi-table atomic transactions without custom RPCs. The bot will need to update the `portfolio` and insert into `trades` sequentially. The `--dry-run` flag will simply log these intents instead of sending the DB mutations.
- **Rate Limiting**: Finnhub's free tier has rate limits (e.g., 60 calls/minute). Concurrency should be capped or throttled if more assets or frequent runs are added.

## 4. Conclusion (Implementation Strategy)

### Proposed Architecture & File Structure
```text
/bot
├── .env.example
├── requirements.txt
├── main.py                # CLI entry point, argument parsing, concurrency handling
├── config.py              # Environment variables (FINNHUB_KEY, GEMINI_API_KEY, SUPABASE_URL, SUPABASE_KEY)
├── clients/
│   ├── finnhub_client.py  # Fetches /quote and recent data
│   ├── gemini_client.py   # Generates BUY/SELL/HOLD decision + justification using Structured Outputs
│   └── supabase_client.py # Reads portfolio state, writes trades, updates balances
└── trading_logic.py       # Order sizing, portfolio validation, dry-run toggling
```

### API Patterns
- **Finnhub Client**: Exposes a `get_market_context(symbol)` returning current price, daily high/low, and latest headlines.
- **Gemini Client**: Uses `google-genai`. We define a Pydantic schema:
  ```python
  class TradeDecision(BaseModel):
      action: Literal["BUY", "SELL", "HOLD"]
      justification: str
  ```
  The prompt provides the asset, current price, and recent data, requesting the `TradeDecision`.
- **Supabase Client**: 
  - `get_portfolio()`: Retrieves all rows mapping `asset_symbol` -> `balance`.
  - `execute_trade(symbol, action, quantity, price)`: Updates USD, updates Asset balance (UPSERT), inserts to `trades`.

### Order Calculation Logic
1. **Fetch State**: Get current USD balance and holdings from `portfolio`.
2. **Concurrent Analysis**: For each asset in `[XAU/USD, AAPL, TSLA, MSFT, GOOGL, AMZN]`, fetch Finnhub data and query Gemini.
3. **Sequential Execution** (to protect USD balance):
   - **If HOLD**: Do nothing.
   - **If BUY**: 
     - Check if `USD balance > 0`.
     - Calculate trade value: `min(10,000, USD balance * 0.1)`. (e.g. use 10% of portfolio or fixed $10k max).
     - Calculate quantity: `trade value / current price`.
     - If `--dry-run`, print intention. If live, deduct USD, add Asset, log Trade.
   - **If SELL**:
     - Check `portfolio` for the asset. If `balance > 0`:
     - Sell 100% of held quantity.
     - Revenue = `quantity * current price`.
     - If `--dry-run`, print intention. If live, add USD, set Asset balance to 0, log Trade.

## 5. Verification Method
1. Inspect the written `handoff.md` to ensure it contains architecture, file structure, API patterns, and order calculation logic.
2. The implementer can use this structured guide to generate the codebase in `/bot`.
3. They will verify functionality by running `python bot/main.py --dry-run` and ensuring no DB writes occur, followed by a live run to verify Supabase updates.
