# Handoff Report: Trade Size Logic Fix Strategy

## 1. Observation
- `bot/trading/engine.py:22` calculates `base_allocation = float(portfolio["USD"]) * 0.10` *before* the trade evaluation loop begins.
- `bot/trading/engine.py:27` iterates sequentially through `decisions.items()`.
- Within the loop (line 45-55), `BUY` orders use `allocated_usd = min(base_allocation, usd_balance)`, which relies on the statically computed `base_allocation`.
- `SELL` orders (lines 74-84) increase `usd_balance` but do *not* recalculate `base_allocation`.
- `bot/test_engine.py` and `bot/test_trade_logic.py` currently test `BUY`-only scenarios and assert that sequential execution yields the expected sizes without considering `SELL`-then-`BUY` order or zero-start `USD` scenarios.

## 2. Logic Chain
1. Because `base_allocation` is fixed before the loop, any `SELL` that occurs inside the loop will increase the local `usd_balance` but cannot change `base_allocation`.
2. Therefore, if `portfolio["USD"]` is initially `$0`, `base_allocation` is `$0`. A `SELL` may free up capital, but subsequent `BUY`s in the same execution cycle will use `min(0, usd_balance)`, evaluating to `$0`. This is the "Zero-Start Bug".
3. Additionally, a large sequence of `BUY`s might sequentially drain `usd_balance` without allowing it to replenish first if `SELL`s happen to appear later in the dict iteration order.
4. To solve this and prevent race conditions (maintaining atomic, sequential DB updates per trade), a two-pass approach over the decisions must be taken: first process all `SELL` decisions (and update `portfolio["USD"]`), *then* dynamically calculate `base_allocation = float(portfolio["USD"]) * 0.10`, and finally process all `BUY` decisions.

## 3. Caveats
- No deep examination of the `HOLD` decision processing was made; it can logically remain in either pass or be ignored, as it doesn't affect portfolio balances.
- The strategy assumes atomicity of DB operations is maintained by keeping `upsert_portfolio_balance` and `insert_trade` inside the loop for each individual trade sequentially (as requested by previous sprint constraints).
- Mock dictionary ordering in Python 3.7+ preserves insertion order, so tests must explicitly craft the dictionary or we must enforce the logic via two independent loops regardless of input order.

## 4. Conclusion
The implementation requires modifying `bot/trading/engine.py::process_decisions` to use a two-pass evaluation loop. 
### Fix Strategy (Code Changes Needed):
1. **Engine modification (`bot/trading/engine.py`)**:
   - Split `decisions.items()` into two lists/iterables: `sells` and `buys`.
   - **Pass 1:** Iterate over `sells`. Execute all `SELL` operations (update local `usd_balance` and `asset_balance`, and execute DB statements).
   - **Recalculation:** Recompute `base_allocation = float(portfolio["USD"]) * 0.10` using the newly freed up USD.
   - **Pass 2:** Iterate over `buys`. Execute all `BUY` operations using `allocated_usd = min(base_allocation, usd_balance)`.
   - Process `HOLD` decisions whenever convenient (e.g. before, during, or after the passes).
2. **Test Updates (`bot/test_engine.py`, `bot/test_trade_logic.py`)**:
   - Add a "Zero-Start Bug" test where initial `USD` is `0`, a `SELL` is provided, and a `BUY` is provided. Assert the `BUY` receives 10% of the `SELL` proceeds.
   - Update existing `test_trade_size_logic` and `test_trade_sizes_equal` to account for the new two-pass structure if they test order-dependent behavior.

## 5. Verification Method
- Implement the changes in `bot/trading/engine.py`.
- Run `python -m unittest bot.test_engine` and `python -m unittest bot.test_trade_logic`.
- Ensure a new test case explicitly validates that if `decisions` has a `BUY` listed *before* a `SELL`, the `SELL` is still processed first and correctly funds the `BUY`.
