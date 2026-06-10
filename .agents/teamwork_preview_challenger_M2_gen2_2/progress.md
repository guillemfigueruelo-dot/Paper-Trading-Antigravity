# Challenger Progress

**Last visited:** 2026-06-10T16:55:00Z

- Created workspace `.agents/teamwork_preview_challenger_M2_gen2_2`.
- Reviewed `bot/trading/engine.py` and the implementer's tests (`test_concurrency.py`, `test_dust.py`).
- Identified that the implementer's concurrency tests used heavy mocking (`patch('bot.trading.engine.update_portfolio_balance_optimistic', return_value=True)`) which bypassed the actual race conditions.
- Wrote `concurrency_oracle_2.py` to stress-test the 3-retry optimistic locking logic. Verified that multiple concurrent trades fail and drop because 3 retries are insufficient when contending for the single `USD` balance row.
- Wrote `race_condition_oracle.py` to test asset balance integrity. Verified that because the optimistic lock ONLY checks `USD` and blind-upserts the asset balance, concurrent BUY/SELL or BUY/BUY on the same asset causes a lost update and destroys the asset balance.
- Wrote `value_destruction_oracle.py` to test the float dust fix. Verified that rounding `qty_to_sell` to 6 decimals works, but the bot then blindly upserts `0.0` as the new asset balance, permanently wiping out any remaining dust (e.g. `0.0000004`) without USD compensation.
- Documented findings in `handoff.md`.
- Ready to send message to main agent.
