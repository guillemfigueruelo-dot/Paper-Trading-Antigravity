# Handoff Report

## 1. Observation
### A. Layout Compliance Violation
The Forensic Auditor reported an integrity violation due to `.py` and `.js` source files existing inside the `.agents/` directory, which strictly mandates only metadata be stored there.
Executing `Get-ChildItem -Recurse -Path .agents -Include *.py,*.ts,*.js,*.db,*.csv | Select-Object FullName` yields exactly 11 violating files (e.g., `auditor_bot_m2/read_hex.py`, `challenger_bot_m2_2/stress_test.py`, `implementer_1/generate_tests.py`).

### B. Functional Bugs in Trading Engine
Verification agents found 3 bugs in `bot/trading/engine.py`:
1. **Concurrency Race Condition:** Updates to `portfolio["USD"]` and `portfolio[symbol]` are read, modified locally, and written back via sequential `upsert` operations (lines 56-73, 109-127), which is not transactional.
2. **Zero-Quantity Trades:** On BUY operations, extremely small `usd_balance` values > 0 are processed. `quantity` is rounded to 6 decimals (line 105), resulting in `0.0`. The script then proceeds to record a 0-quantity trade.
3. **Floating-Point Value Drift:** On BUY operations, the engine deducts `allocated_usd` from the portfolio (line 110) instead of the actual cost `quantity * current_price`, leading to drift between the rounded asset value and the deducted USD.

### C. Test Integrity Violation
The reviewer found that the `tests/e2e/` suite contains auto-generated dummy tests (e.g., `test_f4_execution.py`) with commented-out assertions (`# assert result.returncode == expected_code`), returning a deceptive 100% pass rate without actually asserting anything.

## 2. Logic Chain
1. **Layout**: The project's Layout protocol explicitly forbids source/test scripts in `.agents/`. The 11 files violate this, causing the audit failure.
2. **Race Condition**: Without a DB-side transaction, two bot instances running simultaneously will overwrite each other's balance updates.
3. **Zero-Quantity & Drift**: Floating-point limitations cause microscopic allocations to yield `0.0` trades, and mismatching the deducted cost with the rounded acquired quantity causes financial drift over time.
4. **Test Integrity**: Commented-out assertions are evaluated as passing tests by `pytest`, misleading the audit phase regarding actual system health.

## 3. Caveats
- Moving transactions to Supabase RPC requires creating a Postgres function. If the database schema cannot be altered by the bot right now, optimistic concurrency control (e.g., version columns) or strict lock mechanisms might be needed instead. However, RPC is the most robust fix.
- Deleting the `tests/e2e/` folder removes test coverage, but since it is fake coverage, it is better to have zero E2E tests than fake passing ones. The `bot/` tests remain valid and passing.

## 4. Conclusion
**Verdict:** The current codebase has an integrity violation regarding layout compliance, an integrity violation regarding fake tests, and three logic flaws in the trading engine.

**Concrete Next Steps for Worker:**
1. **Layout Compliance Fix:** Delete the 11 identified script files located inside the `.agents/` directory recursively.
2. **Race Condition Fix:** Shift balance deduction and asset allocation to a Supabase PostgreSQL RPC function to handle the entire trade atomically, and update `bot/trading/engine.py` to call it via `client.rpc()`.
3. **Zero-Quantity Fix:** In `bot/trading/engine.py`, add a guard clause `if quantity <= 0: continue` after calculating the buy/sell quantity to prevent empty trades.
4. **Value Drift Fix:** In `bot/trading/engine.py`, calculate `actual_cost = quantity * current_price` and deduct `actual_cost` instead of `allocated_usd` from the USD balance.
5. **Test Integrity Fix:** Delete the entire `tests/e2e/` directory to remove the fake stub tests. Optionally, replace it with a single genuine E2E test file.

## 5. Verification Method
- **Layout:** Run `Get-ChildItem -Recurse -Path .agents -Include *.py,*.ts,*.js,*.db,*.csv` from the root; it must output nothing.
- **Engine Logic:** Execute `python -m pytest bot` after modifying `engine.py` to ensure unit tests still pass. Perform a `--dry-run` to trace math outputs manually.
- **Test Integrity:** Run `python -m pytest tests/e2e/`. It should either fail with a "directory not found" error or execute genuine tests with assertions.
