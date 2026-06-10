# Synthesized Fix Strategy: Python Trading Bot (Iteration 3)

## Context
The previous iteration failed the empirical challenge because:
1. **Zero-Start Bug & Reinvestment Failure**: `base_allocation` was statically set *before* the loop. A `SELL` could increase the USD balance, but subsequent `BUY`s would still use the original `base_allocation`, meaning newly freed capital couldn't be reinvested in the same run.
2. **Sequential Starvation**: If there are >10 BUYs, a flat 10% base allocation will drain the USD balance completely, starving the remaining assets.
3. Concurrency issues: DB writes must remain sequential to prevent race conditions on the single `USD` balance row.

## Implementation Fixes
Modify `bot/trading/engine.py` to use a two-pass processing logic:

1. **Pass 1 - Process SELLs**:
   - Loop over decisions and execute all `SELL` actions first.
   - Update `portfolio["USD"]` and `portfolio[symbol]` locally.
   - If not `dry_run`, execute the Supabase `upsert` and `insert` statements for the SELL.

2. **Calculate Dynamic Allocation**:
   - Calculate the number of `BUY` decisions: `num_buys = sum(1 for d in decisions.values() if d.action == "BUY")`
   - If `num_buys > 0`:
     - Instead of a flat 10%, calculate `base_allocation = float(portfolio["USD"]) / num_buys`.
     - *Wait*, to maintain the 10% rule but avoid starvation if there are >10 buys: `base_allocation = min(float(portfolio["USD"]) * 0.10, float(portfolio["USD"]) / num_buys)`. 
     - *Actually, the prompt instructed to just use 10% of the NEW usd_balance.* Let's stick to the prompt's instruction: `base_allocation = float(portfolio["USD"]) * 0.10` using the NEW `usd_balance` after SELLs. (We accept starvation as a mathematical consequence if >10 assets, since we only have 6 assets in this project).

3. **Pass 2 - Process BUYs**:
   - Loop over decisions and execute all `BUY` actions sequentially.
   - `allocated_usd = min(base_allocation, portfolio["USD"])`
   - Update `portfolio["USD"]` and `portfolio[symbol]` locally.
   - If not `dry_run`, execute the Supabase `upsert` and `insert` statements for the BUY.

4. **Pass 3 - Process HOLDs**:
   - Loop over decisions and print HOLD actions.

5. **Test Updates**:
   - Update `test_engine.py` and `test_trade_logic.py` to reflect the two-pass logic.
   - Add a specific test case simulating a 0 USD start, one SELL that frees up USD, and one BUY that successfully uses the new USD balance.

## MANDATORY INTEGRITY WARNING
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.
