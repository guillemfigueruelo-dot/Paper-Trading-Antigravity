# Dashboard Implementation Plan

## 1. Project Initialization & Tooling
- **Command:** `npm create vite@latest dashboard -- --template react-ts`
- **Location:** `c:/Users/Figue/Desktop/Paper Trading Antigravity/dashboard`
- **Dependencies:** 
  - `npm install @supabase/supabase-js`
  - `npm install tailwindcss postcss autoprefixer` (and run `npx tailwindcss init -p`)
  - `npm install lucide-react date-fns` (for icons and date formatting)

## 2. Supabase Integration
- **Client setup:** Create `src/lib/supabase.ts`.
  ```typescript
  import { createClient } from '@supabase/supabase-js';
  export const supabase = createClient(
    import.meta.env.VITE_SUPABASE_URL,
    import.meta.env.VITE_SUPABASE_ANON_KEY
  );
  ```
- **Environment:** Require `.env` in the `/dashboard` directory.

## 3. Data Requirements & Fetching
The application will need React `useEffect` hooks to load data from Supabase.
- **USD Balance & Portfolio:** 
  - Query: `supabase.from('portfolio').select('*')`
  - Split results: `USD` balance goes to the main display. Everything else goes to the Asset Portfolio table.
- **Trade History:** 
  - Query: `supabase.from('trades').select('*').order('executed_at', { ascending: false })`
  - *Data Gap Identified:* The database schema in `db/init.sql` does not have a column for AI justifications. The query should select the `justification` column but gracefully fallback to "No justification recorded" if it's missing or null.
- **Overall Performance:**
  - Logic: Baseline is $100,000 (from `db/init.sql`).
  - Total Current Value = USD Balance + Value of Assets. 
  - Since real-time prices are not natively in the DB without fetching Finnhub on the frontend, the easiest proxy is to use the `price_usd` from the most recent trade in the `trades` table for each asset, or have the bot update a `current_value` field in `portfolio`. Given current schema, using the last traded price is the best frontend-only approach.

## 4. UI Components
- **`Dashboard` (Main Container):** Grid layout.
- **`OverviewCards`:** 
  - Card 1: USD Balance.
  - Card 2: Total Estimated Value.
  - Card 3: Overall Return (%).
- **`PortfolioTable`:** Columns for Asset, Quantity.
- **`TradesTable`:** Columns for Date, Type (BUY/SELL), Asset, Quantity, Price, Total Value, and **Justification**.

## 5. GitHub Pages Deployment Configuration
- **Vite Config (`vite.config.ts`):** 
  - Set the `base` path property. Since GitHub Pages serves out of `https://<username>.github.io/<repo-name>/`, `base: '/<repo-name>/'` is required. If the repo name is unknown or variable, `base: './'` is a safer default.
- **GitHub Actions (`.github/workflows/deploy.yml`):**
  - Trigger on push to `main`/`master` paths: `dashboard/**`.
  - Steps: Checkout, setup Node, npm ci (in `/dashboard`), npm run build.
  - Use `actions/upload-pages-artifact` and `actions/deploy-pages`.
