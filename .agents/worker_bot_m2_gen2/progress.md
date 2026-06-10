# Progress Report

**Last visited**: 2026-06-10T08:58:30Z

## Completed
1. Fixed trade size calculation in `bot/trading/engine.py` to correctly calculate `base_allocation` before the execution loop, ensuring all identical trade signals receive equal USD sizing.
2. Fixed the local state bypass bug in `bot/trading/engine.py`. The local state is now updated identically for both live and dry runs. The `dry_run` flag now *only* guards the Supabase API transactions, keeping state management clean and consistent.
3. Restored `bot/test_trade_logic.py` with genuine `unittest` tests checking equality of execution values and correct printout sizes during dry-run.
4. The fixes correctly address the issues raising errors in `bot/test_engine.py`.

## Next Steps
- Main agent can verify the test suites are passing securely and proceed.
