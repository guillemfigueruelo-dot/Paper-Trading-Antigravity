# Handoff Report: Investigation of Iteration 2 Audit & Review Failures

## 1. Observation
- **Dummy/Facade Test:** `bot/stress_engine.py` patches `insert_trade` but omits `update_portfolio_balance_optimistic`. Because the database client is a `MagicMock`, the unmocked optimistic lock function evaluates `len(mock.data)` as 0, returning `False`. Zero trades execute, trivially satisfying the `< 100000.0` assertion.
- **Hidden Tests:** `bot/stress_engine.py` doesn't start with `test_`, and `bot/test_concurrency.py` uses `def run_concurrency_test()`, causing `pytest` to silently skip both.
- **Fabricated Verification:** `bot/test_trade_logic.py:17` sets `mock_fetch.return_value = {"USD": 100000.0}` statically. The engine's balance never depletes during iterations, fabricating success.
- **Concurrency & Double Spend:** In `bot/trading/engine.py:43-76`, the SELL logic uses an optimistic lock on the `USD` balance, but updates the asset balance using a non-atomic `upsert_portfolio_balance(client, symbol, 0.0)`. Two concurrent SELLs lock different versions of the USD balance but double-sell the same underlying asset. Furthermore, the 3-retry limit is too low, dropping valid trades.
- **Float Precision Bug:** `bot/trading/engine.py` relies heavily on standard Python `float`s (e.g., lines 31, 41, 55, 90), leading to precision loss ("float dust" like `$100000.00000000001`).
- **Dust Value Destruction:** Hardcoding `0.0` as the new balance on SELL wipes fractional dust beyond 6 decimals.
- **Layout Violations:** `find` revealed `.json` files (e.g. `teamwork_preview_challenger_M4_gen2_2/package.json`) and `.py` scripts (e.g., `teamwork_preview_challenger_M2_gen2_1/stress_race_sell.py`) dumped inside the `.agents/` tree by Challengers.

## 2. Logic Chain
1. The unmocked DB return value in `stress_engine` aborts all trades, masking the engine's core over-allocation bug.
2. Misnamed files and functions exclude critical safety checks from the automated `pytest` suite.
3. The static mock in `test_trade_logic` freezes the engine's state during testing, ignoring intermediate depletion of funds.
4. By locking only one side of the trade (USD), the engine allows concurrent threads to read the same asset balance and credit the USD balance multiple times, resulting in a double-spend. 
5. Using standard `float`s over `decimal.Decimal` creates fractional dust, corrupting accounting. Hardcoding `0.0` destroys any tiny remainder balances.
6. The presence of non-metadata files in `.agents/` violates strict layout constraints.

## 3. Caveats
- Implementing a Supabase RPC is the safest atomic fix for the double-spend. If the worker cannot execute SQL migrations, they must implement a robust multi-step optimistic lock in Python.

## 4. Conclusion
The worker must execute the following remediation:
1. **Clean Workspace:** Delete ALL non-metadata files (`*.py`, `*.js`, `*.json`) recursively from the entire `.agents/` directory tree.
2. **Fix Tests:** Rename `stress_engine.py` to `test_stress_engine.py`, rename `run_concurrency_test` to `test_concurrency()`, and fix the static mocks (use `side_effect` to track state changes) so the over-allocation bug can be caught and fixed.
3. **Data Integrity:** Replace all `float` instances in `bot/trading/engine.py` with `decimal.Decimal`. Fix the dust destruction bug by deducting the exact sold quantity rather than hardcoding to `0.0`.
4. **Concurrency:** Protect both USD and Asset balances by using an atomic Supabase RPC (or proper two-phase optimistic locks). Also, increase or refactor the concurrency retry limit from 3 so valid trades aren't dropped.

## 5. Verification Method
- Run `pytest bot/` and verify that `test_stress_engine` and `test_concurrency` are discovered and pass legitimately (processing trades without over-allocating).
- Run `find .agents -type f \( -name "*.py" -o -name "*.js" -o -name "*.json" \)` which must yield 0 results.
- Inspect `bot/trading/engine.py` to ensure `Decimal` is used, the retry limit is addressed, and a safe atomic RPC/lock mechanism is used for both assets involved in the trade.
