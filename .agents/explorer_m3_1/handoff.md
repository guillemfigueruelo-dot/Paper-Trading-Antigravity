# Handoff Report: Milestone 3 (React/Vite Dashboard)

## 1. Observation
- Read `PROJECT.md`, `.agents/sub_orch_m3/SCOPE.md`, and `db/init.sql`.
- The user requires a React/Vite dashboard in `/dashboard` displaying USD balance, portfolio, performance, and trade history with AI justifications.
- `db/init.sql` (lines 1-17) defines the `portfolio` table (`asset_symbol`, `balance`, `updated_at`) and `trades` table (`id`, `asset_symbol`, `trade_type`, `quantity`, `price_usd`, `total_value_usd`, `executed_at`).
- `db/init.sql` (lines 35-38) seeds the initial USD balance at $100,000.
- **Critical gap:** The `trades` table schema does not currently contain an `ai_justification` or `justification` column. Milestone 2 (Python bot) is still `IN_PROGRESS` (`PROJECT.md` line 20), so the bot implementer might be the one adding this column.

## 2. Logic Chain
- To fulfill the React/Vite requirement, the `/dashboard` folder should be scaffolded using `npm create vite@latest dashboard -- --template react-ts`.
- To interact with Supabase natively, the `@supabase/supabase-js` package must be utilized.
- To display the USD balance and other assets, the application should query `portfolio` and separate 'USD' from other `asset_symbol`s.
- To calculate "overall performance", the initial seed ($100,000) will serve as the baseline. Since real-time market prices are not stored in the DB, the frontend must estimate the current value of the portfolio using the `price_usd` from the latest `trades` record for each asset.
- Because the `justification` column is not yet in the schema, the frontend must query it tentatively and implement a fallback (e.g., "N/A" or "No justification recorded") to prevent UI crashes if the column is missing or null.
- For GitHub Pages deployment, `vite.config.ts` needs a `base` property configured, and a deploy workflow will be required in `.github/workflows/`.

## 3. Caveats
- The exact GitHub repository name is unknown, so the `base` property in `vite.config.ts` might default to `'./'` or need an explicit repository name adjustment during the CI/CD phase.
- Asset valuation is an estimate. Without a live Finnhub API connection on the frontend, "performance" relies on the last executed trade price.
- The `justification` text is assumed to be added later by the Python Bot milestone (M2). The dashboard will only display it once it exists in the database.

## 4. Conclusion
The implementation plan for the React/Vite dashboard is finalized and documented in `analysis.md`. The implementer can proceed to create the project in `/dashboard`. The frontend should use TailwindCSS for styling and `@supabase/supabase-js` for data access. It must specifically handle the missing `justification` data gracefully and compute portfolio performance using historical trade prices until a live price feed or backend valuation is available.

## 5. Verification Method
- **Build Check:** Run `cd dashboard && npm i && npm run build` to verify the project compiles correctly.
- **Config Check:** Run `view_file` on `dashboard/vite.config.ts` to confirm the `base` attribute is present.
- **Integration Check:** Inspect `dashboard/src/lib/supabase.ts` for valid `VITE_SUPABASE_URL` injection.
- **Fault Tolerance:** Run the app locally (or inspect components) to ensure the trade history table renders successfully even when `justification` data is `undefined` in the Supabase payload.
