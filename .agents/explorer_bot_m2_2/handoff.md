# Handoff Report: Python Trading Bot Implementation Strategy

## Observation
- The project is an Automated Paper Trading System with a Supabase DB (`portfolio`, `trades`).
- The Python Bot must reside in `/bot`.
- It must connect to Finnhub (for prices and recent data) and Gemini API (for structured decisions: BUY/SELL/HOLD + justification).
- It must process multiple assets (XAU/USD, AAPL, TSLA, MSFT, GOOGL, AMZN) simultaneously.
- It must calculate viable trade sizes and execute updates in Supabase.
- It must support a `--dry-run` flag.

## Logic Chain
1. **Concurrency**: To "process multiple assets simultaneously", an `asyncio` loop with `aiohttp` (for Finnhub) and the async features of `google-genai` (for Gemini) is optimal. This allows concurrent data fetching and LLM inference.
2. **Database Integrity**: While reads and LLM inferences can be concurrent, DB updates should be processed sequentially in the Python script to prevent race conditions on the central `USD` balance in the `portfolio` table.
3. **API Patterns**:
   - *Finnhub*: Use standard REST endpoints (`/quote` for prices, `/company-news` or `/crypto/candles` depending on the asset) to gather context.
   - *Gemini*: Use structured outputs (via Pydantic schema) to force the LLM to return `{"action": "BUY|SELL|HOLD", "justification": "..."}`.
   - *Supabase*: Use `supabase-py`. To make a trade, update the `USD` balance, update the `asset` balance (UPSERT), and insert the `trades` record.
4. **Order Calculation Logic**:
   - **BUY**: Fixed position sizing (e.g., 10% of currently available USD) to prevent a single asset from consuming the entire balance. Quantity = `Allocated_USD / Current_Price`.
   - **SELL**: Sell 100% of current holding. Quantity = `Current_Asset_Balance`. If balance is 0, ignore (no short selling).
   - **HOLD**: No action.
5. **Dry-Run**: A `--dry-run` CLI argument will intercept the Supabase DB write step, logging the calculated order to stdout instead of mutating the database.

## Caveats
- **Symbol Formatting**: "XAU/USD" in Finnhub requires a specific broker prefix (e.g., `OANDA:XAU_USD`). The bot should use a mapping dictionary between standard symbols and Finnhub symbols.
- **Transactional Safety**: The `supabase-py` SDK does not support multi-table transactions out-of-the-box via REST. Updates to `portfolio` and `trades` will be sequential HTTP calls. If one fails, the DB could be in an inconsistent state. For a paper trading bot, this may be acceptable, but wrapping the execution in a Supabase Postgres RPC would be safer.
- **Finnhub Rate Limits**: Free tier allows 60 calls/minute. Processing 6 assets concurrently x2 endpoints (quote + news) = 12 calls. This is well within limits, but retries should be implemented.

## Conclusion
The bot should be implemented using Python's `asyncio`. The proposed architecture and file structure are as follows:

### Proposed File Structure (`/bot`)
```
/bot
├── .env.example
├── requirements.txt      # aiohttp, google-genai, supabase, pydantic
├── main.py               # CLI entry point, arg parsing (--dry-run), asyncio loop
├── config.py             # Environment variables and symbol mapping
├── clients/
│   ├── finnhub.py        # Async data fetching (quotes & news)
│   ├── gemini.py         # Structured prompt execution
│   └── supabase_db.py    # DB read/writes
└── trading/
    └── engine.py         # Order calculation & execution orchestration
```

### Proposed Order Calculation & Execution Flow
1. Fetch all asset current prices and contexts concurrently.
2. Fetch Gemini decisions concurrently.
3. Fetch current `USD` and asset balances from Supabase.
4. Process each decision sequentially:
   - If **BUY**: Check `USD` > 0. Allocate 10% of `USD`. `qty = (USD * 0.1) / price`. 
   - If **SELL**: Check `Asset_Balance` > 0. `qty = Asset_Balance`.
   - If not valid, drop trade.
5. If not `--dry-run`:
   - Update `portfolio` (subtract USD, add Asset for BUY; vice versa for SELL).
   - Insert into `trades`.

## Verification Method
1. Create a mock script or test suite that triggers `main.py --dry-run`.
2. Inspect stdout to ensure all 6 assets are processed.
3. Verify that the DB balances are not mutated during a dry-run.
4. Run without `--dry-run` and verify `portfolio` and `trades` tables in Supabase reflect the expected changes.
