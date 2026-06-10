## 2026-06-10T16:41:09Z
Read c:\Users\Figue\Desktop\Paper Trading Antigravity\.agents\teamwork_preview_orchestrator_M2\SCOPE.md.
Implement the following fixes for the Python Trading Bot based on Explorer's findings:
1. `bot/clients/finnhub_client.py`: Update data fetching to retrieve recent historical candles (e.g. 5-10 days of history) from Finnhub to append to the quote data. Ensure you handle endpoints correctly for different asset types (e.g. Forex vs Stocks).
2. `bot/clients/gemini_client.py`: Update the AI prompt to include the recent data (candles) to allow proper trend analysis. Sanitize the LLM JSON response by stripping markdown blocks (e.g. ```json ... ```) before `json.loads`.
3. `bot/trading/engine.py`: 
   - If `fetch_portfolio` raises an exception and `dry_run=False`, abort execution. Do not use a dummy fallback if we intend to write to the DB.
   - If `fetch_portfolio` returns an empty dict (not a read error), immediately seed Supabase with an initial 100,000.00 USD balance.
   - Round the `quantity` for BUYs and SELLs to a safe decimal limit (e.g., 6 decimal places) before updating the database.

Run the build and test commands (e.g. `pytest`) to verify your changes. Document commands and results in your handoff report.
