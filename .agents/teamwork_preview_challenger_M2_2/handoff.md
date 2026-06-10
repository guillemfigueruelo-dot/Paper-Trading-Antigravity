# Handoff Report: Python Trading Bot Verification

## 1. Observation
- In `bot/test_concurrency.py`, when simulating concurrent executions of `process_decisions()`, the output states: `"RACE CONDITION CONFIRMED: One update overwrote the other!"`. We observed that `engine.py` fetches the USD balance into memory, calculates the new balance, and then issues `upsert_portfolio_balance()` without transactional locks.
- In `bot/generator_random_trades.py`, the test logs contain instances like: `ACTION: BUY 0.000000 SYM_X for $0.00`. A microscopic amount of USD triggered the conditional `if usd_balance > 0:` due to floating-point imprecision.
- In `bot/trading/engine.py`, Pass 2 (BUYs), the code computes `quantity = round(allocated_usd / current_price, 6)`. However, it updates the USD balance via `portfolio["USD"] = usd_balance - allocated_usd`, instead of subtracting the exact cost (`quantity * current_price`). We tested this locally with `current_price = 6.0` and `allocated_usd = 10000.0`: the bot credits `1666.666667` shares but only subtracts `$10000.00` from the USD balance, despite the true cost being `$10000.000002`.

## 2. Logic Chain
1. **Concurrency Race Condition**: Because the bot may run on a CRON schedule via GitHub Actions, overlapping runs could occur. The lack of optimistic concurrency control or row-level locking during the "read-modify-write" flow in `engine.py` guarantees lost updates if executions overlap.
2. **Zero-Quantity Trades**: The bot allocates 10% of the initial USD balance for each asset. When buying >10 assets, the balance should perfectly hit $0.0 after the 10th buy. Due to IEEE-754 floating-point inaccuracy, the remainder is typically a tiny fraction (e.g., `3.49e-10`). This satisfies `if usd_balance > 0`, leading to an allocation so small that rounding it to 6 decimal places yields 0 shares. The database then receives a junk trade with 0 quantity.
3. **Floating-Point Value Drift**: Because the database deducts the pre-rounded `allocated_usd` rather than the exact value of the shares acquired (`quantity * current_price`), every BUY trade creates a tiny mismatch between the asset value acquired and the USD deducted. Over thousands of trades, this inflates or deflates the total portfolio value out of thin air.

## 3. Caveats
- The concurrency issue assumes that the bot might execute simultaneously (e.g. if the user configures the CRON job too frequently or if a job hangs). If strict singleton execution is enforced at the GitHub Actions level, the race condition is mitigated, though the logic is fundamentally unsafe.
- The floating-point value drift is small (micro-cents per trade), but breaks strict financial invariants.

## 4. Conclusion
The Python trading bot logic has three critical flaws:
1. **CRITICAL**: Vulnerable to race conditions leading to lost DB updates under concurrent execution.
2. **MEDIUM**: DB bloat from inserting 0-quantity trades due to floating-point conditions.
3. **MEDIUM**: Breaks financial double-entry invariants by deducting estimated allocation instead of actual cost.

## 5. Verification Method
1. **Concurrency**: Run `python bot/test_concurrency.py` to observe the `RACE CONDITION CONFIRMED` failure mode.
2. **Zero-Quantity**: Run `python bot/generator_random_trades.py` multiple times until the output prints `ACTION: BUY 0.000000 ... for $0.00`.
3. **Value Drift**: Execute a script calling `process_decisions()` with a $6.00 quote and a "BUY" action. Observe that the user acquires 1666.666667 shares (value: $10000.000002) but the USD balance decreases by exactly $10000.00.
