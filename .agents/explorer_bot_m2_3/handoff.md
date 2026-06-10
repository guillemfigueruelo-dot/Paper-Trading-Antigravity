# Handoff Report: Python Trading Bot Implementation Strategy

## 1. Observation
- `PROJECT.md` mandates a Python bot located in `/bot` that fetches market data from Finnhub for XAU/USD, AAPL, TSLA, MSFT, GOOGL, AMZN.
- It must consult the Google AI Studio (Gemini) API for structured trading decisions (BUY, SELL, HOLD) accompanied by a justification.
- The bot must connect to Supabase (using `db/init.sql` schema: `portfolio` and `trades` tables) to update balances and log trades.
- Requirements include processing multiple assets simultaneously and supporting a `--dry-run` CLI flag.
- `SCOPE.md` specifies using `supabase-py` and `google-genai` (or `google-generativeai`), and requires a `requirements.txt` and `.env.example`.

## 2. Logic Chain
1. **Concurrency**: To satisfy the "process multiple assets simultaneously" requirement efficiently, Python's `asyncio` is the optimal choice. It allows non-blocking network I/O when communicating with Finnhub and Gemini.
2. **AI Decisions**: For deterministic integration, Gemini must output structured JSON. The newer `google-genai` SDK supports strict JSON outputs via Pydantic models, which perfectly fits the need for an Enum decision (BUY, SELL, HOLD) and a string justification.
3. **Data Fetching**: Finnhub requires distinct API calls per asset. An async HTTP client like `aiohttp` is necessary to fetch quotes concurrently without blocking the event loop.
4. **Order Calculation**: The bot needs concrete logic to size trades. Since it reads the `portfolio` table, it can determine available USD. A robust approach is fixed-size USD buys (e.g., $1000 per trade) to ensure we don't exhaust funds in a single trade, and selling 100% of the held asset position upon a SELL signal.
5. **Database Consistency**: While fetching data and AI decisions can be done concurrently, executing the trades (updating USD balance, updating asset balance, logging trade) should be done sequentially per asset at the end of the run to prevent race conditions on the shared USD balance in the `portfolio` table.

## 3. Caveats
- **Finnhub Symbol for Gold**: The exact Finnhub symbol for XAU/USD needs to be identified and tested (often `OANDA:XAU_USD` or similar in forex feeds) since it's not a standard US equity ticker.
- **Database Transactions**: `supabase-py` REST API does not natively support multi-table atomic transactions easily. The bot will perform sequential API calls to insert into `trades` and upsert into `portfolio`. In a cron-triggered script, this is usually acceptable, but mid-execution failures could leave the database partially updated.
- **Finnhub Rate Limits**: The free tier of Finnhub limits API calls per second. Requesting 6 assets concurrently should fall well within limits, but it's worth noting if the asset list grows.

## 4. Conclusion

### Proposed Architecture
- **Execution Model**: A single-shot async process triggered by standard OS cron or GitHub Actions.
- **Concurrency**: An `asyncio` event loop that spawns concurrent tasks for data fetching and AI evaluation using `asyncio.gather()`.
- **State Flow**:
  1. Initialize DB client and read current portfolio state (USD + asset holdings).
  2. Launch parallel tasks for each of the 6 assets to fetch Finnhub data and query Gemini.
  3. Await all results.
  4. Sequentially process the decisions: recalculate available USD, calculate trade sizes, and execute Supabase mutations.
  5. If `--dry-run` is active, skip Supabase mutations and print the intended actions to standard output.

### File Structure (`/bot`)
```text
/bot
├── main.py            # CLI entry point (argparse), async event loop orchestration
├── config.py          # Environment variables management (os.getenv or pydantic-settings)
├── market_data.py     # Finnhub API async interactions (using aiohttp)
├── ai_decision.py     # Gemini API integration (google-genai + Pydantic schema)
├── database.py        # Supabase client wrapper (read portfolio, execute trades)
├── requirements.txt   # Dependencies: supabase, google-genai, aiohttp, pydantic
└── .env.example       # Template for SUPABASE_URL, SUPABASE_KEY, FINNHUB_API_KEY, GEMINI_API_KEY
```

### API Patterns
- **Finnhub**: Use `aiohttp` to `GET https://finnhub.io/api/v1/quote?symbol={symbol}`.
- **Gemini**: Use `google_genai.AsyncClient`. Pass a Pydantic model as `response_schema` (e.g., `class Decision(BaseModel): action: Literal["BUY", "SELL", "HOLD"]; justification: str;`).
- **Supabase**: Use `supabase.create_async_client` (available in newer versions) or run standard synchronous `supabase.create_client` calls in `asyncio.to_thread()`.

### Order Calculation Logic
- **BUY**: 
  - Check available USD. If USD < $1,000, skip (insufficient funds).
  - Target Trade Value = $1,000 (or a configurable default).
  - Quantity = Target Trade Value / Current Price (from Finnhub).
- **SELL**:
  - Check current asset holding in portfolio. If holding <= 0, skip (nothing to sell).
  - Quantity = 100% of current holding.
  - Total Value USD = Quantity * Current Price.
- **HOLD**:
  - Do nothing. Log the justification if desired.
- **Execution**: Deduct/add USD from `portfolio`, upsert the `asset_symbol` balance in `portfolio`, and insert the record into `trades`.

## 5. Verification Method
- **Implementation Check**: Verify that `main.py --dry-run` executes successfully, logs the Finnhub prices, Gemini decisions, and calculated order sizes for all 6 assets concurrently without altering Supabase.
- **Data Validation**: Confirm via `curl` or browser that Finnhub returns valid data for the chosen XAU/USD symbol string before hardcoding it.
- **DB Test**: Verify `supabase-py` operations match the `init.sql` schema exact column names and constraints.
