# Investigation Handoff

## Observation
1. In `bot/trading/engine.py:22`, `base_allocation = float(portfolio["USD"]) * 0.10` is statically calculated before iterating over any trade decisions.
2. Inside the decision loop in `bot/trading/engine.py:45-73`, `BUY` and `SELL` decisions are processed sequentially in a single pass. If a `SELL` executes, it increases the `usd_balance` locally (line 82), but the `base_allocation` is not re-evaluated for subsequent `BUY` decisions. This causes the "Zero-Start Bug", where an initial USD balance of $0 leads to a `base_allocation` of $0, even if assets are sold.
3. In `bot/trading/engine.py:47`, the calculation `allocated_usd = min(base_allocation, usd_balance)` is used to determine trade size. If there are many `BUY` signals (e.g., > 10), the first 10 will exhaust the USD balance, starving the rest (Sequential Starvation).
4. Tests in `bot/test_engine.py` and `bot/test_trade_logic.py` currently test the single-pass sequential evaluation. They do not simulate scenarios with concurrent `SELL` and `BUY` decisions where the proceeds of the `SELL` are expected to fund the `BUY`.

## Logic Chain
- To fix the "Zero-Start Bug" and ensure reinvestment, all `SELL` decisions must be executed first so that the `usd_balance` is fully replenished before any capital is allocated to new `BUY` decisions.
- After all `SELL` decisions are processed and `portfolio["USD"]` is updated, `base_allocation` should be calculated as 10% of the *new* `portfolio["USD"]`.
- Processing `BUY` decisions in a second pass sequentially using the updated `base_allocation` and `usd_balance` ensures that capital freed up by sells can be immediately reinvested.
- The use of `allocated_usd = min(base_allocation, usd_balance)` prevents overdrawing the account, naturally handling the "Sequential Starvation" by executing as many full 10% allocations as possible and then using any remaining fractions before skipping the rest.
- The tests in `bot/test_engine.py` and `bot/test_trade_logic.py` must be updated to cover a scenario where the initial balance is $0, a `SELL` is executed, and a subsequent `BUY` successfully utilizes the newly freed capital.

## Caveats
- Sequential starvation is partially retained by design: if there are more than 10 `BUY` signals, the 11th onwards will likely have a $0 `usd_balance` and be skipped. This behavior appears intended as long as no negative balance is created.
- `HOLD` decisions should be placed in the second pass for logging purposes so that they don't print prematurely.
- Concurrency race conditions are mitigated by strictly enforcing sequential evaluation within the `bot/trading/engine.py` state loop instead of firing async database updates.

## Conclusion
Refactor `process_decisions` in `bot/trading/engine.py` to use a two-pass evaluation:
1. **Pass 1:** Iterate over `decisions.items()`. Process only `SELL` actions, updating local `portfolio["USD"]` and `portfolio[symbol]`, and committing trades to DB.
2. **Re-calculate:** Set `base_allocation = float(portfolio["USD"]) * 0.10` using the updated balance.
3. **Pass 2:** Iterate over `decisions.items()`. Process `BUY` actions (using `min(base_allocation, usd_balance)`) and `HOLD` actions.
Update `bot/test_engine.py` and `bot/test_trade_logic.py` to assert this new two-pass logic, including a test case specifically for reinvesting capital from a SELL.

## Verification Method
1. Modify `bot/trading/engine.py` with the two-pass fix.
2. Update unit tests in `bot/test_engine.py` and `bot/test_trade_logic.py` to assert the expected execution order (SELLs before BUYs) and correct trade sizes based on the recalculated `base_allocation`.
3. Run the test suite: `python -m unittest bot/test_engine.py bot/test_trade_logic.py`.
4. The tests should pass and confirm that capital from a `SELL` is immediately available and accurately factored into the new `base_allocation` for subsequent `BUY` decisions.
