# Progress

Last visited: 2026-06-10T08:50:00Z

- Initialized workspace.
- Explored `bot/trading/engine.py` and `bot/main.py`.
- Found the bot uses a sequential loop to process decisions.
- Created `test_engine.py` to test trade size logic. Observed that allocations shrink because the 10% is computed against the remaining USD balance, not the initial USD balance.
- Created `test_concurrency.py` to test concurrent behavior. Observed that a race condition occurs, dropping updates to the USD balance because `portfolio['USD']` is fetched once per task and blindly upserted.
- Formulating the `handoff.md` with a FAIL verdict.
