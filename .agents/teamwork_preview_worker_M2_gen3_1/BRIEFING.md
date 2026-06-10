# BRIEFING — 2026-06-10T16:57:02Z

## Mission
Fix layout compliance by deleting source code in `.agents`, refactor fake/hidden tests in `bot/` to use pytest, and fix bot logic regarding floating point dust and concurrency in `bot/trading/engine.py`.

## 🔒 My Identity
- Archetype: Teamwork agent
- Roles: implementer, qa, specialist
- Working directory: c:\Users\Figue\Desktop\Paper Trading Antigravity\.agents\teamwork_preview_worker_M2_gen3_1
- Original parent: 716dc283-ae27-4f49-9ff7-15a193c0c719
- Milestone: M2

## 🔒 Key Constraints
- DO NOT CHEAT. All implementations must be genuine.
- DO NOT hardcode test results, expected outputs, or verification strings in source code.
- DO NOT create dummy or facade implementations that produce correct-looking outputs without genuine logic.
- DO NOT circumvent the intended task.
- Ensure state consistency and genuine behavior.

## Current Parent
- Conversation ID: 716dc283-ae27-4f49-9ff7-15a193c0c719
- Updated: 2026-06-10T16:57:02Z

## Task Summary
- **What to build**: Fix layout (delete .agents py/js/json files), refactor tests (`bot/stress_engine.py`, `bot/test_concurrency.py`, `bot/test_trade_logic.py`), fix engine logic (`bot/trading/engine.py` using Decimal, atomicity/optimistic locking, precise quantity sold, increase retry limits).
- **Success criteria**: Pytest passes for `bot/`, .agents directory contains no source files, engine is concurrency-safe.

## Key Decisions Made
- Delete files using Get-ChildItem and Remove-Item.

## Artifact Index
- [TBD]
