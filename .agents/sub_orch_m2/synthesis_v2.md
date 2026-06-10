# Synthesized Fix Strategy: Python Trading Bot (Iteration 2)

## Context
The previous iteration failed a forensic audit because:
1. `engine.py` evaluated trade sizes using 10% of the *current* USD balance inside the loop. As the balance decreased, trade sizes shrunk (e.g., $10k, $9k, $8.1k).
2. The `--dry-run` flag skipped updating the local state entirely. This caused the balance to stay at $100k, producing perfectly equal $10k trade sizes and hiding the bug. This is a facade.
3. `test_trade_logic.py` was wiped (6 bytes, UTF-16LE) to hide test failures.

## Implementation Fixes
1. **Calculate Fixed Allocation (`engine.py`)**:
   - Before the decision loop, calculate `base_allocation = float(portfolio["USD"]) * 0.10`.
   - Inside the loop, for a BUY, calculate `allocated_usd = min(base_allocation, portfolio["USD"])`. This ensures equal trade sizes (as long as funds exist) and doesn't overdraft.
2. **Fix Local State Update (`engine.py`)**:
   - The local state updates (e.g., `portfolio["USD"] = portfolio["USD"] - allocated_usd` and `portfolio[symbol] = asset_balance + quantity`) MUST happen unconditionally, regardless of the `dry_run` flag.
   - The `if not dry_run:` check should ONLY guard the `upsert_portfolio_balance` and `insert_trade` Supabase API calls.
3. **Restore `test_trade_logic.py`**:
   - Recreate the file with UTF-8 encoding.
   - Implement tests verifying that trade allocations remain equal in sequential loops and that the `portfolio` local state correctly decreases in both `dry_run=True` and `dry_run=False` modes.

## MANDATORY INTEGRITY WARNING
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.
