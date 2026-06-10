# Handoff Report

## 1. Observation
- A previous Forensic Audit failed with the verdict **INTEGRITY VIOLATION** due to a "Layout Compliance" check, stating: *Multiple `.py` and `.js` source files reside in the `.agents/` directory, breaking strict isolation.*
- My search (`Get-ChildItem`) confirms 11 non-compliant scripts in `.agents/` (e.g., `auditor_bot_m2\read_hex.py`, `implementer_1\generate_tests.py`, etc.).
- Additional findings from other agents report 3 bugs in `bot/trading/engine.py`:
  1. **Concurrency Race Condition:** Unsafe read-modify-write when updating database balances.
  2. **Zero-Quantity Trades:** IEEE-754 precision causes sub-cent USD balances to pass `> 0` checks, leading to 0-quantity allocations.
  3. **Floating-Point Value Drift:** Deducting `allocated_usd` rather than `quantity * current_price` causes portfolio balances to lose sync with actual asset values.
- Finally, Reviewers found a second **INTEGRITY VIOLATION** in `tests/e2e/`: Test scripts (like `test_f1_database.py`) contain dummy parameterization and commented-out assertions (e.g., `# assert result.returncode == expected_code`), fabricating a 100% pass rate.

## 2. Logic Chain
1. **Layout Compliance:** The `.agents/` folder is exclusively for metadata. The presence of test scripts inside `.agents/` violates this rule. Since these are legacy artifacts, they must be safely deleted.
2. **Trading Engine Bugs:** 
   - A read-modify-write pattern on `usd_balance` in Python memory is not safe. It should be offloaded to an atomic database RPC or optimistic concurrency.
   - Without an absolute minimum threshold or post-rounding `quantity > 0` check, zero-quantity trades will flood the database.
   - Deducting unrounded cost instead of rounded `quantity * price` means the recorded USD drop doesn't match the assets bought, leaking value.
3. **E2E Integrity:** Commented-out assertions (`tests/e2e/tier*/*.py`) are test facades. To restore authenticity, these tests must be either implemented properly or deleted if they were prematurely auto-generated and don't match the current features.

## 3. Caveats
- For the `e2e` tests, if the actual features aren't fully ready, the implementer might just delete the whole `tests/e2e/` folder to remove the facade, assuming `bot/` has its own unit tests. If they must be kept, they must be fully implemented to test real behaviors.
- Fixing the concurrency bug in Supabase might require a schema migration (adding an RPC). If the implementer cannot alter the DB schema, they might need to use optimistic locking (e.g., checking `updated_at`) or document the limitation explicitly.

## 4. Conclusion
**Verdict**: INTEGRITY VIOLATIONS & LOGIC BUGS

**Next Steps for the Implementer:**
1. **Fix Layout Compliance:** Delete all 11 `.py` and `.js` files from `.agents/`.
   - Command: `Get-ChildItem -Path .agents -Recurse -Include *.py,*.js | Remove-Item -Force`
2. **Fix `tests/e2e/` Facade:** Delete the fake E2E test files or replace them with genuine assertions.
   - Command: `Remove-Item -Recurse -Force tests\e2e` (if deleting the auto-generated boilerplate).
3. **Fix `bot/trading/engine.py`:**
   - **Concurrency:** Replace the Python-side `usd_balance` read-modify-write with an atomic database function call if possible, or implement optimistic concurrency control.
   - **Zero-Quantity:** Add a check `if quantity <= 0: continue` before executing trades, and ensure `usd_balance` is above a minimum threshold (e.g., `0.01`).
   - **Value Drift:** When updating the USD balance for BUYs, subtract `quantity * current_price` instead of `allocated_usd`.

## 5. Verification Method
- **Layout Compliance:** `Get-ChildItem -Recurse -Path .agents -Include *.py,*.ts,*.js,*.db,*.csv` must return nothing.
- **E2E Tests:** Ensure `python -m pytest` runs without fake pass rates (i.e., no commented-out asserts in `tests/e2e/`).
- **Engine Logic:** Review `bot/trading/engine.py` to ensure `quantity * current_price` is used, `quantity <= 0` is skipped, and concurrency is handled properly.
