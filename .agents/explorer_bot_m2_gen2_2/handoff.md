# 1. Observation
- `bot/trading/engine.py` (lines 44-54) calculates `allocated_usd = usd_balance * 0.10` inside the loop. Since `usd_balance` is sequentially deduced in live runs, subsequent BUY actions receive shrinking allocations (e.g., $10,000, then $9,000).
- `bot/trading/engine.py` (lines 50-68 and 79-97) wraps both the local dictionary state updates (`portfolio["USD"] = ...`) and the database updates (`upsert_portfolio_balance`) inside `if not dry_run:`.
- `bot/test_engine.py` has a test `test_trade_size_logic` which legitimately fails because it expects trade sizes to be equal in live execution. 
- `bot/test_trade_logic.py` is a 6-byte empty file (UTF-16LE), clearly intentionally wiped to suppress test failures that would have exposed the discrepancy between dry-run and live modes.

# 2. Logic Chain
1. **The Allocation Bug**: Because `allocated_usd` is evaluated dynamically based on the continually decreasing `usd_balance`, trade sizes shrink instead of maintaining an equal distribution.
2. **The Facade**: By skipping the local state update in `--dry-run` mode, `usd_balance` never decreases. It stays at $100,000 for the entire loop, meaning every trade allocates exactly $10,000. This perfectly masks the sequential shrinking bug that occurs in live execution, violating the principle that tests and dry runs should mirror real execution paths.
3. **The Fix Strategy - Allocation**: To achieve equal allocations without breaking sequential safety, the engine should determine a `base_allocation` using 10% of the **initial** USD balance at the start of the execution cycle. It must then apply `allocated_usd = min(base_allocation, usd_balance)` to ensure we do not over-draft the account if funds run low.
4. **The Fix Strategy - Dry Run**: To eliminate the facade, the local state dictionary updates (`portfolio["USD"] = ...`, `portfolio[symbol] = ...`) must be moved **outside** the `if not dry_run:` block. Only external side-effects (database `upsert` and `insert`) should be guarded.
5. **The Fix Strategy - Tests**: The wiped `test_trade_logic.py` must be rewritten. It must contain tests verifying that `dry_run=True` correctly updates the local portfolio dictionary, and tests ensuring equal trade sizing independent of evaluation order.

# 3. Caveats
- The changes proposed modify core trading allocation logic. If more than 10 simultaneous BUY signals occur, the `min(base_allocation, usd_balance)` safeguard will correctly cap the final trades, meaning the 11th trade might be smaller or 0. This is the intended and mathematically safe behavior.
- I have provided the explicit code to drop into `test_trade_logic.py` but have not executed it directly due to read-only investigation constraints.

# 4. Conclusion
The bot intentionally hides a sequential logic bug by diverging its local state behavior during `--dry-run` and wiping the test suite that would catch it. The fix requires decoupling the target allocation amount from the sequentially updated balance, applying state updates locally regardless of execution mode, and restoring the test files to explicitly assert against this facade behavior.

# 5. Verification Method
1. **Implement Engine Fixes**: In `bot/trading/engine.py`, store `initial_usd_balance = float(portfolio["USD"])` before the loop. Update BUY logic to `allocated_usd = min(initial_usd_balance * 0.10, usd_balance)`. Move all `portfolio` local dictionary updates outside `if not dry_run:`.
2. **Implement Test Fixes**: Overwrite `bot/test_trade_logic.py` with the content in `.agents/explorer_bot_m2_gen2_2/proposed_test_trade_logic.py` (which I have generated to verify both the equal allocation and the dry-run state behavior).
3. **Execute Verification**: Run `python -m unittest bot/test_engine.py` and `python -m unittest bot/test_trade_logic.py`. Both should pass, and the output logs for a dry run should now correctly mirror the live run's state deduplication.
