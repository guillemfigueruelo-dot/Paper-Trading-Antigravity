# Trading Bot Analysis Handoff

## Observation
- `bot/clients/gemini_client.py:16` explicitly uses the model `gemini-2.5-flash` in the API URL, which does not exist and will result in an HTTP error.
- `bot/clients/finnhub_client.py:7` only fetches data from the `/api/v1/quote` endpoint. It fetches current prices and daily stats, but does not fetch time-series "recent data" (such as historical candles) as requested by the requirements.
- `bot/config.py:12` defines the correct asset list: `["XAU/USD", "AAPL", "TSLA", "MSFT", "GOOGL", "AMZN"]`. It also maps `XAU/USD` to `OANDA:XAU_USD` for Finnhub.
- `bot/main.py:18-26` uses `asyncio.gather` to fetch quotes and Gemini decisions concurrently, fulfilling the multi-asset requirement.
- `bot/trading/engine.py` processes trade decisions sequentially. It correctly validates viability: SELLs liquidate existing asset balances, and BUYs dynamically allocate up to 10% of the available `usd_balance`.

## Logic Chain
1. **Concurrency**: The bot correctly satisfies the concurrency requirement by querying external APIs (Finnhub, Gemini) in parallel. It avoids database race conditions by executing trades sequentially in `engine.py`.
2. **Order Viability**: The logic in `engine.py` is sound. It checks available `USD` for buys and caps them at the 10% base allocation, and checks available asset balances for sells.
3. **Gemini API Error**: The Gemini API call will inevitably fail because `gemini-2.5-flash` is an invalid model string. Changing it to `gemini-1.5-flash` or `gemini-2.0-flash` is strictly required for the bot to generate decisions.
4. **Recent Data Gap**: The prompt explicitly asks for "recent data". The `/quote` endpoint only provides a daily snapshot. To fulfill this, `finnhub_client.py` must be extended to pull historical candles and append this history to the context sent to Gemini. 

## Caveats
- **Finnhub Endpoints**: Finnhub's API structure distinguishes between stocks and forex for candles. Implementing the "recent data" fetch will require handling `OANDA:XAU_USD` (using the `/api/v1/forex/candle` endpoint) differently than the US stocks (using the `/api/v1/stock/candle` endpoint).
- **Supabase Schema**: The Supabase schema was not independently verified, but the client methods `upsert` and `insert` match the interface contracts defined in `SCOPE.md`.
- **API Keys**: I executed a dry-run test without actual API keys. My conclusions on API responses are based on the codebase logic and known API versioning.

## Conclusion
The core concurrency, trade math, and Supabase integration are well-implemented. The primary issues preventing the bot from meeting all requirements are the invalid Gemini model version and the lack of historical "recent data" fetched from Finnhub.

**Concrete Next Steps for the Worker:**
1. **Fix Gemini Client**: In `bot/clients/gemini_client.py`, update the Gemini model string in the URL to a valid version (e.g. `gemini-1.5-flash` or `gemini-2.0-flash`).
2. **Enhance Finnhub Client**: Update `bot/clients/finnhub_client.py` to fetch recent historical data (e.g., past 7 days of daily candles) using Finnhub's candle endpoints (`/stock/candle` for equities and `/forex/candle` for Forex). Merge this historical data into the dictionary returned by `fetch_quote`.
3. **Update Prompt**: Ensure the prompt in `gemini_client.py` explicitly asks the AI to consider both the current price and the recent historical data when formulating its structured decision.

## Verification Method
- **Run dry-run**: Update the API keys in a local `.env` file and execute `python bot/main.py --dry-run`.
- **API Validation**: Verify that there are no HTTP 400/404 errors from the Gemini API and that the AI returns valid JSON.
- **Context Inspection**: Print the `prompt` string in `gemini_client.py` before sending the request to verify it contains the recent historical candle data.
- **Run Tests**: Execute `python -m unittest bot.test_engine bot.test_trade_logic bot.test_concurrency bot.generator_random_trades` to ensure no regressions in trade math.
