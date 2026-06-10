# Handoff Report: Python Trading Bot Integrity Violation Fix Strategy

**Core Finding**: The bot suffers from a sequential shrinking bug because it calculates trade allocation as a percentage of the continuously updated remaining balance rather than the initial balance. The `--dry-run` mode hides this by bypassing local state updates entirely. The `test_trade_logic.py` file was wiped to hide the resulting test failures.

## 1. Observation
- **`bot/trading/engine.py` (lines 40-41, 44-46)**: In the `process_decisions` loop, `usd_balance` is fetched via `float(portfolio["USD"])` and `allocated_usd` is calculated as `usd_balance * 0.10`.
- **`bot/trading/engine.py` (lines 50-53)**: Local state is only updated if `not dry_run` is true. `portfolio["USD"] = usd_balance - allocated_usd` is skipped during a dry run, meaning `portfolio["USD"]` never changes across multiple trades in dry run mode.
- **`bot/test_engine.py` (lines 47-48)**: A test explicitly checks for equality in trade sizes (`self.assertEqual(executed_trades[0]['total_value_usd'], executed_trades[1]['total_value_usd'])`) and has the comment: "Trade sizes shrink due to sequential evaluation of balance!". This test fails when `process_decisions` is executed with `dry_run=False`.
- **`bot/test_trade_logic.py`**: The file is 6 bytes and effectively empty, matching the auditor's description of a wiped file to bypass tests.

## 2. Logic Chain
1. **The Sequential Bug**: Because `allocated_usd` is 10% of the *current* `usd_balance` inside the loop, the first trade takes 10% of $100k ($10k), leaving $90k. The second trade takes 10% of $90k ($9k), resulting in shrinking trades. The requirement expects equal trade allocations.
2. **The Facade Bug**: In `--dry-run` mode, since the local `portfolio` state is not updated, `usd_balance` remains at $100k for all loop iterations. Thus, `allocated_usd` is calculated as $10k every time, falsely producing "equal" trades and hiding the sequential bug.
3. **The Test Wiping**: `test_trade_logic.py` was likely the original suite that tested trade allocation sizes and dry-run state behavior. Since it failed due to the bugs, it was wiped to forcefully pass CI/CD or the audit gate.

## 3. Caveats
- Since `test_trade_logic.py` is empty, its original test cases are lost. We will have to infer the necessary tests from scratch.
- The `git log` command timed out, preventing me from recovering the original contents of the wiped test file.
- It is assumed that 10% of the *initial* USD balance is the intended target for "equal trade allocations."

## 4. Conclusion
To restore integrity without breaking functionality, we must apply three fixes:
1. **Equal Trade Sizing**: Calculate `initial_usd_balance = float(portfolio["USD"])` *before* the `for symbol, decision in decisions.items():` loop in `bot/trading/engine.py`. Inside the loop, calculate `allocated_usd = initial_usd_balance * 0.10`. Use a constraint like `if usd_balance >= allocated_usd:` to ensure we don't overspend.
2. **Fix Dry-Run State**: Move the local state updates (`portfolio["USD"] = usd_balance - allocated_usd`, etc.) *outside* of the `if not dry_run:` block. The `if not dry_run:` block should only guard the external DB calls (`upsert_portfolio_balance` and `insert_trade`). This ensures the internal simulation matches reality.
3. **Restore Tests**: Recreate `bot/test_trade_logic.py` to contain unit tests verifying that:
   - Trade allocations remain equal across consecutive BUY operations.
   - The local state `portfolio["USD"]` decreases accurately even when `dry_run=True`.
   - No database calls are made when `dry_run=True`.

## 5. Verification Method
- **Method**: After the implementer applies the code changes:
  1. Inspect `bot/trading/engine.py` to ensure `initial_usd_balance` is calculated outside the loop and local `portfolio` updates occur unconditionally.
  2. Inspect `bot/test_trade_logic.py` to ensure robust unit tests assert the expected dry-run and trade sizing logic.
  3. Run the tests using `python -m unittest bot.test_engine bot.test_trade_logic`. Both suites must PASS without any test-wiping or mock facades.
