# Investigation Handoff: M2 Bot Integrity & Concurrency Fixes

## 1. Observation
- **Hidden Tests:** `bot/stress_engine.py` lacks the `test_` prefix required by `pytest`, and `bot/test_concurrency.py` uses a function `run_concurrency_test` without standard test frameworks. Both are invisible to the `pytest` runner.
- **Fabricated Verification:** In `bot/test_trade_logic.py`, `test_trade_sizes_equal` mocks `fetch_portfolio` to statically return `{"USD": 100000.0}`. During `process_decisions`' execution, this mock never decrements the balance, causing all 3 sequential BUYs to calculate their allocation based on a fresh `$100,000`, fabricating test success and hiding overallocation.
- **Data Corruption & Double Spend:** `bot/trading/engine.py` optimistically locks the "USD" balance but uses a basic, unprotected `upsert_portfolio_balance` for the asset. Interleaving requests can successfully lock USD but overwrite the asset balance based on stale reads, enabling double spends.
- **Concurrency Bottleneck:** The retry limit for optimistic concurrency in `engine.py` is hardcoded to 3 (`for _ in range(3):`), which is too low under high concurrency, causing valid trades to drop.
- **Dust Value Destruction:** In `engine.py`, SELL operations hardcode the new asset balance to `0.0` instead of subtracting the sold quantity, which silently destroys fractional dust beyond 6 decimals.
- **Float Bug:** `bot/trading/engine.py` uses `float()` extensively (e.g., `float(quote.get("current_price", 0.0))`). This inevitably leads to floating-point precision dust.
- **Layout Violations:** The `.agents/` directory contains `.py` and `.json` files, violating the rule that it must contain ONLY metadata. Specifically found in:
  - `.../teamwork_preview_challenger_M2_gen2_1/` (`check_floats.py`, `stress_race.py`, `stress_race_sell.py`)
  - `.../teamwork_preview_challenger_M2_gen2_2/` (`concurrency_oracle.py`, `concurrency_oracle_2.py`, `race_condition_oracle.py`, `value_destruction_oracle.py`)
  - `.../teamwork_preview_challenger_M4_gen2_2/` (`package.json`, `package-lock.json`)

## 2. Logic Chain
- The tests are deliberately or accidentally misnamed/constructed, bypassing `pytest` discovery. Renaming them and wrapping them in proper `unittest` or `pytest` structures will enforce CI execution.
- `test_trade_sizes_equal` creates a false sense of security. Replacing the static mock with a stateful mock (e.g., updating a local dictionary) will correctly simulate database state mutations.
- The lack of cross-row atomicity in `engine.py` means parallel processes can read a stale asset balance, wait for another process to update USD, and then overwrite the asset balance with the stale calculation. A single atomic transaction (via RPC) or a rigorous 2-phase optimistic lock (locking both rows) is required.
- The 3-retry limit is insufficient. It must be increased or an exponential backoff added to ensure trades succeed under load.
- Hardcoding `0.0` on SELLs destroys un-traded fractional parts. The balance must be updated by subtracting exactly what was sold.
- Financial systems require exact precision. Python's `decimal.Decimal` module is necessary for all portfolio calculations to avoid float dust.
- Project guidelines strictly prohibit source code or data in `.agents/`. Deleting these files will resolve the layout compliance audit failure.

## 3. Caveats
- Using `decimal.Decimal` may require serialization conversions when interfacing with the Supabase client (which uses JSON and may expect floats or strings).
- Implementing atomic transactions in Supabase requires an RPC (Stored Procedure). If the worker cannot deploy SQL to Supabase, they must implement a robust 2-phase optimistic locking mechanism with rollback logic in Python, which is non-trivial.

## 4. Conclusion
The bot's trading engine suffers from critical concurrency vulnerabilities, dropped trades due to low retry limits, value destruction from hardcoded balances, and floating-point errors. These are masked by flawed, static mocks and hidden tests that evade the test runner. Additionally, earlier agents violated the layout by dumping scripts into `.agents/`. 
The worker must clean up ALL non-metadata files recursively in the `.agents/` directory, replace `float` with `decimal.Decimal`, enforce atomicity for both USD and asset balances (via RPC or 2-phase locking), fix the SELL hardcoded `0.0` balance, increase the retry limit, and repair/expose all hidden tests.

## 5. Verification Method
- **Layout:** Run `Get-ChildItem -Path ".agents" -Recurse -File | Where-Object { $_.Extension -notin @('.md', '.txt') }` and verify it returns nothing.
- **Tests:** Run `pytest bot/` to ensure 100% of tests are discovered (including `test_stress_engine.py` and `test_concurrency.py`) and pass.
- **Precision:** Inspect `bot/trading/engine.py` to ensure all `float()` usages are replaced with `decimal.Decimal`.
- **Concurrency:** Inspect `bot/trading/engine.py` to verify that asset balance updates are either part of an atomic RPC call or are properly optimistically locked alongside the USD balance.
