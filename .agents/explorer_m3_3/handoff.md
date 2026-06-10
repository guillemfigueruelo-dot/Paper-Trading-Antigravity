# Handoff Report: Milestone 3 (React/Vite Dashboard) Explorer

## 1. Observation
- The project scope (`PROJECT.md` and `SCOPE.md`) requires a React/Vite dashboard in `/dashboard` displaying Supabase data: USD balance, asset portfolio, overall performance, and a table showing trade history with AI justifications.
- The dashboard must be configured for GitHub Pages deployment.
- Examined `/db/init.sql`. The database schema has two tables:
  - `portfolio`: `asset_symbol`, `balance`, `updated_at`.
  - `trades`: `id`, `asset_symbol`, `trade_type`, `quantity`, `price_usd`, `total_value_usd`, `executed_at`.
- The `trades` table does NOT contain a column for AI justifications (e.g., `ai_justification TEXT`).
- There is no table or API endpoint within the current `init.sql` schema to track current market prices, making accurate "overall performance" calculations on the frontend dependent on either past trades or an external API.

## 2. Logic Chain
- To meet the requirement of reading from Supabase and displaying the requested data, we need to initialize a Vite React application in `/dashboard` and install `@supabase/supabase-js`.
- The dashboard will query the `portfolio` table to display USD balance (where `asset_symbol = 'USD'`) and the asset portfolio (where `asset_symbol != 'USD'`).
- The dashboard will query the `trades` table to populate the trade history table.
- Since the schema lacks an `ai_justification` column, the frontend will be unable to display this until the backend/DB schema is updated.
- For overall performance, the simplest approach without an external API is to show a summary of realized values, or evaluate current assets based on their last traded price. Alternatively, the frontend could call the Finnhub API if the key is provided to it via `.env`.
- To deploy to GitHub Pages, the Vite project must be built to a directory (like `dist/`) and configured with the correct `base` path in `vite.config.js`. A GitHub Actions workflow must be created to automate the build and deployment.

## 3. Caveats
- **Missing DB Column:** The `trades` table currently lacks the `ai_justification` column required by the specification. The Database Initialization (M1) is marked as DONE, so this requires an `ALTER TABLE` script or an update to `init.sql`.
- **Overall Performance Calculation:** Current market prices are needed to accurately reflect "overall performance". If the frontend is not supposed to call Finnhub directly, performance might be calculated using historical trade prices, which is inaccurate for unrealized gains.
- **Repository Name:** The `base` path in `vite.config.js` typically needs to match the repository name for GitHub pages (e.g., `/repo-name/`). We will use a placeholder or `/` and adjust upon deployment.

## 4. Conclusion
**Proposed Implementation Plan for `/dashboard`:**

1. **Initialize Project:**
   - Run `npm create vite@latest dashboard -- --template react-ts` from the project root.
   - Install dependencies: `npm install @supabase/supabase-js react-router-dom lucide-react` (for icons) and `tailwindcss` for styling.

2. **Supabase Client Setup (`src/supabaseClient.ts`):**
   - Export a Supabase client configured with `import.meta.env.VITE_SUPABASE_URL` and `import.meta.env.VITE_SUPABASE_ANON_KEY`.

3. **Components:**
   - **`Dashboard.tsx`:** Main container.
   - **`Portfolio.tsx`:** Fetches from `portfolio`. Displays 'USD' balance prominently and other assets in a grid/list.
   - **`PerformanceSummary.tsx`:** Calculates basic performance metrics (e.g., total USD spent vs. current portfolio value based on last trades).
   - **`TradeHistory.tsx`:** Fetches from `trades`. Displays a table. *Note: UI should prepare a column for `Justification` but leave it blank or show a placeholder until the backend adds the column.*

4. **GitHub Pages Configuration:**
   - Update `vite.config.ts` to include `base: './'` (or the exact repo name) for relative asset paths.
   - Add `.github/workflows/deploy-pages.yml` utilizing the `actions/upload-pages-artifact` and `actions/deploy-pages` actions to publish the Vite `dist` directory.

**Action Required:** Propose an update to `/db/init.sql` to add `justification TEXT` to the `trades` table.

## 5. Verification Method
- **Frontend Setup:** Run `cd dashboard && npm install && npm run dev` to verify the React app starts locally.
- **Supabase Connectivity:** Add valid `.env.local` credentials and verify the app successfully fetches data from `portfolio` and `trades` tables.
- **Build & Deploy:** Run `npm run build` and ensure the `dist/` directory is created without type or linting errors.
