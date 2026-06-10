# Handoff Report

## Observation
1. In `bot/trading/engine.py` (lines 44-54), trade sizes are calculated inside the allocation loop as `usd_balance * 0.10`. Because `portfolio["USD"]` is sequentially deducted in normal execution (line 52: `portfolio["USD"] = usd_balance - allocated_usd`), subsequent trade allocations shrink.
2. In `bot/trading/engine.py` (line 50), the local state update is wrapped in `if not dry_run:`. This bypasses the sequential deduction entirely when `--dry-run` is passed, making `usd_balance` remain static and generating falsely equal allocations.
3. `bot/test_engine.py` demonstrates this sequential shrink bug with a legitimate failing test.
4. `bot/test_trade_logic.py` was wiped empty (6 bytes, UTF-16LE, equivalent to `echo "" > test_trade_logic.py`), preventing it from being read as plain text and bypassing the failing tests.

## Logic Chain
1. The `--dry-run` mode prevents local state updates, causing the trade allocation calculation to use the original `usd_balance` for every trade, masking the sequential allocation bug. This constitutes a facade implementation.
2. The sequential allocation bug itself arises because the allocation percentage is recalculated on a shrinking balance instead of being fixed at the start of the execution round.
3. Wiping `test_trade_logic.py` serves as a mechanism to hide these failures (self-certifying test violation) rather than fixing the core business logic.
4. Fixing the bug requires separating the base allocation calculation from the dynamic available balance, allowing equal allocations while accurately modeling the descending available balance in local state, regardless of `dry_run`.

## Caveats
- `bot/test_trade_logic.py` could not be read completely due to a MIME type error (UTF-16LE), but its 6-byte file size directly confirms the auditor's observation that it was wiped.
- No direct external DB checks were performed, as the focus is on the local logic and facade behavior.

## Conclusion
The current implementation intentionally hides a logic defect using a `--dry-run` facade and a wiped test file, resulting in an INTEGRITY VIOLATION.

### Fix Strategy
1. **Calculate Fixed Allocation:** In `bot/trading/engine.py`, calculate `base_allocation = float(portfolio["USD"]) * 0.10` *before* the loop. Inside the loop, use `allocated_usd = min(base_allocation, usd_balance)` to maintain equal trade sizes without risking overdraft.
2. **Fix Local State Update (`--dry-run` bug):** Move the local state updates (`portfolio["USD"] = usd_balance - allocated_usd` and `portfolio[symbol] = asset_balance + quantity`) outside the `if not dry_run:` block. The `dry_run` flag should *only* guard the external Supabase API calls, allowing the local `portfolio` simulation to behave identically in both modes.
3. **Restore `test_trade_logic.py`:** Delete the malformed 6-byte file and recreate it with UTF-8 encoding. Implement tests verifying that trade allocations remain equal in sequential loops and that the `portfolio` local state correctly decreases in both `dry_run=True` and `dry_run=False` modes.

## Verification Method
1. Apply the fixes to `bot/trading/engine.py` and recreate `bot/test_trade_logic.py`.
2. Run `python -m unittest bot/test_engine.py` to ensure the existing failing test now passes (trade sizes no longer shrink).
3. Run `python -m unittest bot/test_trade_logic.py` to ensure local state simulates correctly.
4. Run `python bot/main.py --dry-run` to confirm the mock log output shows sequentially correctly modeled trade sizes without updating the remote DB.
