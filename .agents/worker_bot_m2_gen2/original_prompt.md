## 2026-06-10T08:55:30Z

Implement the fixes for the Python Trading Bot in `/bot`.
Use the fix strategy defined in `c:/Users/Figue/Desktop/Paper Trading Antigravity/.agents/sub_orch_m2/synthesis_v2.md`.
Read `c:/Users/Figue/Desktop/Paper Trading Antigravity/PROJECT.md` for project context.

Requirements:
- Fix the trade size calculation in `bot/trading/engine.py` (calculate base allocation BEFORE the loop).
- Fix the local state update bypass in `bot/trading/engine.py` (update local state regardless of `--dry-run`, only guard DB calls).
- Restore `bot/test_trade_logic.py` and write legitimate unit tests for the logic.
- Ensure `bot/test_engine.py` passes legitimately.

MANDATORY INTEGRITY WARNING: DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Provide a `handoff.md` in `c:/Users/Figue/Desktop/Paper Trading Antigravity/.agents/worker_bot_m2_gen2/` with the verification command used and output.
