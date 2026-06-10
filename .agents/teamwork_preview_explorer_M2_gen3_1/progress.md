## Investigation Complete
- Last visited: 2026-06-10T16:56:43Z
- Reviewed `SCOPE.md`, `bot/stress_engine.py`, `bot/test_concurrency.py`, `bot/test_trade_logic.py`, `bot/trading/engine.py`.
- Discovered why tests were hidden and how fabricated test states passed.
- Analyzed the concurrency bugs (blind asset upsert, 3-retry bottleneck, hardcoded `0.0` value destruction on SELL).
- Confirmed layout violations in `.agents/`.
- Updated `handoff.md` with complete findings.
- Sent message to Orchestrator.
