# Handoff Report

## 1. Observation
- `PROJECT.md` specifies a React/Vite dashboard configured for GitHub pages, pulling from a Supabase database.
- `.agents/sub_orch_m3/SCOPE.md` details the requirement for displaying: USD balance, asset portfolio, overall performance, and a table showing trade history with AI justifications.
- `db/init.sql` (lines 8-17) contains the schema for the `trades` table. It includes `id`, `asset_symbol`, `trade_type`, `quantity`, `price_usd`, `total_value_usd`, and `executed_at`. It **does not** contain a column for AI justifications.
- `db/init.sql` (lines 1-6) contains the schema for the `portfolio` table. It includes `asset_symbol`, `balance`, and `updated_at`.

## 2. Logic Chain
- To fulfill the requirement of reading from Supabase, the dashboard will need `@supabase/supabase-js`.
- The dashboard will be a typical React SPA initialized with Vite.
- For GitHub Pages deployment, the Vite config will need the `base` property set appropriately to match the repository name (or `./` if deployed at the root or relative).
- Since the database schema lacks an `justification` column, the frontend implementation will either need to mock this data, wait for a database migration (to add something like `justification TEXT`), or safely handle undefined values for this field when rendering the "AI justifications" requirement.

## 3. Caveats
- The exact GitHub repository name is unknown, so the `base` path in `vite.config.ts` for GitHub pages deployment might need adjusting later.
- The `justification` column is missing from `trades` in `db/init.sql`. The bot implementation (M2) might add this, or the DB schema (M1) needs to be updated. For now, the frontend must handle this gracefully.
- The calculation for "overall performance" might require live market prices to value non-USD assets correctly. If live prices aren't available to the frontend, it may need to display performance based on the last traded prices or cost basis.

## 4. Conclusion (Implementation Plan)
**Goal:** Create a React/Vite dashboard in `/dashboard` reading from Supabase.

**Step-by-Step Implementation:**
1. **Initialize Project:** Run `npm create vite@latest dashboard -- --template react-ts` in the project root.
2. **Dependencies:** Install `@supabase/supabase-js` for data fetching. Optionally install `lucide-react` for icons and `tailwindcss` for styling.
3. **Supabase Client Setup:** Create `src/lib/supabase.ts` to initialize the client using `import.meta.env.VITE_SUPABASE_URL` and `import.meta.env.VITE_SUPABASE_ANON_KEY`.
4. **Data Fetching:** Create hooks/services to query:
   - `supabase.from('portfolio').select('*')` to get USD balance and asset holdings.
   - `supabase.from('trades').select('*').order('executed_at', { ascending: false })` to get the history.
5. **Components:**
   - **Portfolio Summary:** Display the USD balance (where `asset_symbol === 'USD'`) and a list of other assets.
   - **Trade History Table:** A table rendering rows from `trades`. Include a column for "Justification", and map it to a property like `trade.justification || 'N/A'` to gracefully handle the missing DB schema column.
   - **Overall Performance:** Display metrics aggregating the portfolio and trade history.
6. **GitHub Pages Configuration:** Edit `vite.config.ts` to configure `base: ''` or `./` to ensure static assets load correctly.
7. **Environment variables:** Add `.env.example` inside `/dashboard` documenting the required Supabase keys.

## 5. Verification Method
- From project root, run `cd dashboard && npm install`.
- Provide mocked `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` in `.env.local` to satisfy client init.
- Run `npm run build` and ensure it completes without TypeScript or Vite errors.
- Run `npm run dev` and visually verify the UI renders the data structures defined in the database.
