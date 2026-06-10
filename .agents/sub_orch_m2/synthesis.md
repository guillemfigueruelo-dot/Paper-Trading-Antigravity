# Synthesized Implementation Strategy: Python Trading Bot

## Architecture & Structure
Use Python's `asyncio` to process the 6 assets simultaneously (XAU/USD, AAPL, TSLA, MSFT, GOOGL, AMZN).
Create the bot inside `/bot` with this structure:
```text
/bot
├── .env.example
├── requirements.txt      # aiohttp, google-genai, supabase, pydantic
├── main.py               # CLI entry point (--dry-run), asyncio loop orchestrator
├── config.py             # Env variables, Finnhub symbol mapping (e.g. XAU/USD -> OANDA:XAU_USD)
├── clients/
│   ├── finnhub_client.py # Fetch /quote and recent data (async)
│   ├── gemini_client.py  # Structured Outputs via Pydantic for BUY/SELL/HOLD + justification (async)
│   └── supabase_client.py# Supabase interactions (sync/sequential for safety)
└── trading/
    └── engine.py         # Order sizing & dry-run evaluation
```

## Logic Flow
1. Fetch all asset data from Finnhub concurrently.
2. Query Gemini concurrently using a Pydantic schema: `{"action": "BUY|SELL|HOLD", "justification": "..."}`.
3. Fetch `portfolio` from Supabase (to get USD and asset balances).
4. Process each decision SEQUENTIALLY to protect the `USD` balance from race conditions:
   - **BUY**: If USD > 0, allocate 10% of available USD. `quantity = allocated_USD / current_price`.
   - **SELL**: If Asset balance > 0, sell 100% of it. `quantity = current_asset_balance`.
   - **HOLD**: Skip.
5. If `--dry-run` is active, print the intended trade to stdout.
6. If live, update `portfolio` (USD and Asset balances) and insert the trade record into `trades`.

## Important Caveats
- **MANDATORY INTEGRITY WARNING**: DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.
- Map logical symbols (e.g. `XAU/USD`) to Finnhub symbols for the API, but keep the logical symbol for Supabase records.
