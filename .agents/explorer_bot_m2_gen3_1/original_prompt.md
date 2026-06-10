## 2026-06-10T09:05:13Z
The previous iteration of the Python Trading Bot FAILED the gate due to logic flaws identified by the Challengers. The Forensic Audit was CLEAN.
You must read the codebase in `/bot` and provide a fix strategy.

Feedback from Challengers:
1. "Zero-Start Bug" & Reinvestment Failure: `base_allocation` is statically set based on the `USD` balance *before* any trades occur. If a `SELL` occurs, the USD balance increases, but the `base_allocation` for subsequent `BUY`s remains 0. It cannot dynamically reinvest capital freed up by sells.
2. "Sequential Starvation": `base_allocation` is calculated as 10% of the initial USD balance. If there are >10 BUY signals, it drains the USD balance.
3. Concurrency Race Conditions: Note that the previous synthesis mandated sequential DB updates to avoid race conditions. If testing concurrency, it fails atomicity.

Your task: Provide a fix strategy for `bot/trading/engine.py` to fix the trade size calculation.
A recommended strategy:
- Process all `SELL` decisions FIRST in the loop, updating the local `usd_balance`.
- Then, calculate `base_allocation = float(portfolio["USD"]) * 0.10` using the NEW `usd_balance`.
- Then, process all `BUY` decisions sequentially, each using `allocated_usd = min(base_allocation, usd_balance)`.
- Ensure tests in `test_engine.py` and `test_trade_logic.py` are updated to reflect this two-pass (SELL then BUY) evaluation logic.

Output a `handoff.md` in `c:/Users/Figue/Desktop/Paper Trading Antigravity/.agents/explorer_bot_m2_gen3_1/`.
