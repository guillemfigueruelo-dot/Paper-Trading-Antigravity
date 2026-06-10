# Handoff Report

## Observation
1. **Concurrency Mocking Flaw**: The implementer's test `bot/test_concurrency.py` mocks the core fix by doing `@patch('...update_portfolio_balance_optimistic', return_value=True)`, meaning it completely bypassed validating if the optimistic locking works against real race conditions.
2. **Dropped Trades (Insufficient Retries)**: In `bot/trading/engine.py`, the optimistic lock retries a maximum of 3 times (`for _ in range(3):`). Running `concurrency_oracle_2.py` with 10 concurrent threads buying assets shows that under contention for the shared `USD` balance, many threads exhaust their 3 retries and silently drop the trades, failing to execute.
3. **Asset Balance Race Condition**: In `bot/trading/engine.py`, the optimistic lock ONLY validates the `USD` balance. After claiming the `USD` update, it executes a blind `upsert_portfolio_balance(client, symbol, new_asset)`. Running `race_condition_oracle.py` with 2 concurrent BUYs for the same asset (`AAPL`) shows that one process will overwrite the other's upsert, causing a lost update that destroys the accumulated asset quantity (e.g. paying for 200 AAPL but only receiving 100).
4. **Dust Value Destruction**: In the SELL loop of `bot/trading/engine.py`, the bot calculates `qty_to_sell = round(current_asset, 6)` to avoid Finnhub precision issues. However, after successful execution, it hardcodes the remaining balance: `upsert_portfolio_balance(client, symbol, 0.0)`. Running `value_destruction_oracle.py` with a starting balance of `10.0000004` shows the bot sells `10.0`, gets credited USD for `10.0`, but wipes the remaining `0.0000004` dust to `0.0`, effectively destroying portfolio value without compensation.

## Logic Chain
1. By mocking the optimistic locking outcome in tests, the implementer failed to realize that their lock was incomplete.
2. Because every trade updates the same `USD` row, `USD` becomes a high-contention bottleneck. A fixed limit of 3 retries is statistically insufficient for concurrent bursts (e.g., cron overlaps or multi-container scaled deployments), causing silent trade failures.
3. Because the asset balance is not protected by the optimistic lock or a transaction, concurrent modifications to the same asset suffer from classic Time-Of-Check to Time-Of-Use (TOCTOU) race conditions, violating data integrity.
4. Because the SELL logic hardcodes the final asset balance to `0.0` instead of mathematically subtracting the actual `qty_to_sell` from `current_asset`, any fractional dust truncated by the 6-decimal rounding is permanently lost instead of being retained in the portfolio.

## Caveats
- The concurrency tests were run via synthetic threaded oracles (`concurrency_oracle_2.py`, `race_condition_oracle.py`) mocking the PostgREST network delay. Real network latency might slightly change the exact collision frequency, but the underlying logical flaws remain mathematically certain.
- The `fetch_portfolio` method fetches the entire portfolio on every retry, which is highly inefficient, but functional.

## Conclusion
**FAIL**. The implementer's fixes for both concurrency and float/dust bugs are critically flawed. The optimistic locking implementation causes dropped trades and lost updates on asset balances. The dust fix introduces a new value destruction bug by blindly wiping out unsold fractional shares. The implementer must rewrite the concurrency fix (preferably using Supabase `.rpc()` for atomic PostgreSQL transactions) and fix the SELL logic to subtract `qty_to_sell` rather than hardcoding `0.0`.

## Verification Method
- **Bug 1 (Insufficient Retries)**: Run `$env:PYTHONPATH="."; python .agents/teamwork_preview_challenger_M2_gen2_2/concurrency_oracle_2.py` to see trades drop.
- **Bug 2 (Lost Updates)**: Run `$env:PYTHONPATH="."; python .agents/teamwork_preview_challenger_M2_gen2_2/race_condition_oracle.py` to see the asset balance race condition.
- **Bug 3 (Value Destruction)**: Run `$env:PYTHONPATH="."; python .agents/teamwork_preview_challenger_M2_gen2_2/value_destruction_oracle.py` to see the dust wiped without compensation.
