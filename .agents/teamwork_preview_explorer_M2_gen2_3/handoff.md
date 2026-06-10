# Handoff Report

## 1. Observation
- **Forensic Audit Violation**: The Forensic Auditor failed the implementation due to a Layout Compliance violation. While the `bot/` logic is authentic and functioning, multiple `.py` and `.js` source and test scripts were improperly left inside the `.agents/` directory by previous agents.
- **Reviewer Integrity Violation**: Reviewers identified that the tests in the `tests/e2e/` directory are dummy facade functions with commented-out assertions (e.g., `test_f1_database.py`), artificially returning a 100% pass rate. This violates the strict anti-cheat policy.
- **Challenger Bug Reports**: Challengers found three critical bugs in `bot/trading/engine.py`:
  1. *Concurrency Race Condition*: The engine updates the database using a non-transactional read-modify-write pattern.
  2. *Zero-Quantity Trades*: IEEE-754 precision errors cause microscopic allocations to pass the `usd_balance > 0` check, resulting in `quantity = 0.0` after rounding, which are then inserted as trades.
  3. *Floating-Point Value Drift*: The engine deducts `allocated_usd` rather than the exact cost (`quantity * current_price`), causing the portfolio USD balance to drift over time.

## 2. Logic Chain
1. The `.agents/` directory protocol mandates that it must contain ONLY metadata (e.g., `.md` files). The presence of source code like `read_hex.py` or `stress_test.py` triggered the Forensic Auditor's layout compliance failure.
2. The `tests/e2e/` directory violates the fundamental rule against dummy/facade implementations. Because these tests do not execute actual assertions against the codebase, they must be removed to clear the Reviewer's integrity violation.
3. In `bot/trading/engine.py`, executing a buy trade with `quantity = round(..., 6)` can result in exactly `0.0`. Inserting this into the database creates invalid records.
4. When buying an asset, deducting the initial `allocated_usd` ignores the rounding applied to the quantity, causing a mismatch between the USD deducted and the actual value of the asset purchased (`quantity * current_price`). 
5. To safely run multiple instances or assets concurrently, the portfolio balance must be updated atomically rather than reading the state, modifying it in Python, and overwriting it in the database.

## 3. Caveats
- Fixing the concurrency race condition robustly may require creating a Supabase RPC (Stored Procedure) to handle atomic increments/decrements. If modifying the database schema is out of scope for the worker, they will need to implement an application-level optimistic locking mechanism or clearly document the limitation.
- Removing `tests/e2e/` reduces perceived coverage, but the Forensic Auditor noted that there are 4 genuine tests within the `bot/` directory itself that pass legitimately.

## 4. Conclusion
The worker must implement the following concrete fix strategy:
1. **Layout Compliance Cleanup**: Delete all non-markdown source files (`*.py`, `*.js`, etc.) from the `.agents/` directory to clear the Forensic Audit failure.
2. **Remove Facade Tests**: Delete the entire `tests/e2e/` directory to eliminate the dummy test integrity violation.
3. **Fix Trading Engine Bugs (`bot/trading/engine.py`)**:
   - *Value Drift*: Calculate `actual_cost = quantity * current_price` and deduct this exact amount from the USD balance instead of `allocated_usd`.
   - *Zero-Quantity Trades*: Add an explicit `if quantity > 0:` check before executing any BUY or SELL trade.
   - *Concurrency*: Replace the read-modify-write DB updates with a Supabase RPC call for atomic balance adjustments, or implement an optimistic concurrency check.

## 5. Verification Method
- **Layout Verification**: Run `Get-ChildItem -Recurse -Path .agents -Include *.py,*.ts,*.js,*.db,*.csv` from PowerShell. The output must be completely empty.
- **Integrity Verification**: Check that `tests/e2e/` does not exist and run `python -m pytest bot` to ensure the remaining genuine tests pass.
- **Logic Verification**: Inspect `bot/trading/engine.py` to ensure `actual_cost` is used for USD deductions and `quantity > 0` guards the trade executions.
