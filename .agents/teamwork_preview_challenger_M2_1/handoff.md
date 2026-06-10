# Handoff Report

## 1. Observation

We wrote three empirical test harnesses (`bot/test_rounding.py`, `bot/test_dust.py`, `bot/test_dust_buy.py`) to stress test the trading engine. 
- **Observation 1 (Rounding Bug)**: When running `bot/test_rounding.py`, allocating $10.0 to buy SYM1 at $60.0/share, the engine bought 0.166667 shares (worth $10.00002) but deducted exactly $10.0 from the USD balance. Mismatch: $10.0 != $10.00002.
- **Observation 2 (Dust Crash)**: When running `bot/test_dust.py` (SELL balance of 0.0000004) and `bot/test_dust_buy.py` (BUY with $0.000001 USD), the engine calculated `quantity = 0.0` and `total_value_usd = 0.0`. It then attempted to execute the trade, which violates the database constraint `CHECK (quantity > 0)` in `db/init.sql`.
- **Observation 3 (Finnhub API)**: The `bot/clients/finnhub_client.py` uses the `https://finnhub.io/api/v1/quote?symbol=...` endpoint for all assets. For `OANDA:XAU_USD`, this fails because Finnhub's `/quote` endpoint only supports US stocks. A direct Python request to the Finnhub quote endpoint for forex symbols returns 401.

## 2. Logic Chain

1. In `engine.py`, during a BUY action, `portfolio['USD']` is reduced by `allocated_usd`, while the actual quantity of shares bought is `round(allocated_usd / current_price, 6)`. Because the true cost is `quantity * current_price`, the difference between `allocated_usd` and the true cost is magically created or destroyed. The accounting invariant is broken.
2. In `engine.py`, trades are processed without checking if the rounded `quantity > 0`. A very small remaining balance (dust) results in `quantity = 0.0`, which causes the Supabase client to throw an exception when inserting into `trades` due to postgres constraints, terminating the entire script mid-execution.
3. Finnhub limits `/quote` to US Stocks. Since `engine.py` skips execution if `current_price <= 0`, `XAU/USD` will never be traded by the bot.

## 3. Caveats

- Tests were run using mocks for Supabase to isolate Python engine logic.
- The Finnhub API behavior assumes standard free-tier or basic-tier API keys, where Forex quotes are not supported on the stock `/quote` endpoint. If an enterprise tier magically supports it, Observation 3 might not apply, but documentation says otherwise.

## 4. Conclusion

The implementation contains critical correctness bugs and fails to meet all requirements:
1. **Financial Leak**: The engine breaks accounting invariants due to incorrect float math during BUY operations.
2. **Database Crashes**: Dust balances cause the bot to crash during DB insertions.
3. **Broken Requirement**: `XAU/USD` market data fetching is fundamentally broken due to endpoint mismatch.
Verdict: **FAIL**. The bot logic requires fixing.

## 5. Verification Method

1. Run `.\bot\venv\Scripts\python.exe -m unittest bot.test_rounding` to see the rounding mismatch assertion fail.
2. Run `.\bot\venv\Scripts\python.exe -m unittest bot.test_dust` and `bot.test_dust_buy` to see the zero-quantity assertions fail.
3. Run `python -c "import urllib.request; print(urllib.request.urlopen('https://finnhub.io/api/v1/quote?symbol=OANDA:XAU_USD').getcode())"` to see the Finnhub quote endpoint fail with 401 Unauthorized for forex.
