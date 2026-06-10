# Investigation Report: Dashboard Build and Data Fetching Fixes

## 1. Observation
- `npm run build` currently fails with `TS6133` (unused local/parameter) errors in three test files:
  - `src/App.reactivity.test.tsx`: line 19 (`event`)
  - `src/App.realtime.test.tsx`: line 4 (`supabase`), line 9 (`tradesCallback`), line 42 (`event`, `filter`)
  - `src/App.stress.test.tsx`: line 113 (`element`)
- `npm test` reveals two failing behaviors:
  1. **Reactivity Test Failure**: `App.tsx` calls `setLoading(true)` unconditionally within `fetchData`. Real-time updates trigger `fetchData`, which causes the dashboard UI to be completely unmounted and replaced with "Loading dashboard..." on every update.
  2. **Pagination Test Failure**: The application calculates total portfolio value by finding the latest trade price within the loaded `trades` array. Since Supabase limits queries to 1000 rows by default, an asset whose last trade occurred more than 1000 trades ago will not have its price found, resulting in an incorrect portfolio valuation.

## 2. Logic Chain
1. **TypeScript Errors**: The project uses `"noUnusedLocals": true` and `"noUnusedParameters": true` in `tsconfig.app.json`. To fix these errors, unused parameters should be prefixed with an underscore (e.g. `_event`) or removed if not needed. Unused local variables and imports should be deleted.
2. **Reactivity Bug**: The dashboard should only show a loading screen during the initial load, not when silently updating data in the background. Removing `setLoading(true)` from the body of `fetchData` and instead wrapping the initial call (`setLoading(true); fetchData().finally(() => setLoading(false));`) ensures the UI remains stable during real-time updates.
3. **Pagination Bug & Data Fetching**: Relying on the `trades` array to determine current asset prices is fragile and breaks when trade history exceeds pagination limits. The correct approach is to separate the concerns:
   - Query the `trades` table specifically for the latest price of *each* held asset using `.eq('asset_symbol', asset.symbol).order('executed_at', { ascending: false }).limit(1)`.
   - Store these prices in a separate React state (`prices: Record<string, number>`).
   - Limit the general `trades` query to `.limit(100)` to efficiently display recent history without fetching massive datasets.
   - Calculate `totalPortfolioValue` using the dedicated `prices` state.

## 3. Caveats
- Fetching prices individually for each asset introduces an N+1 query pattern (where N is the number of unique assets in the portfolio). For a paper trading application, the number of unique assets held simultaneously is typically small (e.g., < 20), making `Promise.all` perfectly acceptable. However, if the portfolio grows to hundreds of assets, a custom Supabase database view or RPC function would be more efficient.
- The proposed fix assumes `maybeSingle()` or `single()` is used when fetching the latest price per asset.

## 4. Conclusion
To resolve the build errors and data fetching issues, implement the following changes:
- **Test Files**: Remove the unused `supabase` import and `tradesCallback` variable in `App.realtime.test.tsx`. Prefix unused parameters with `_` in `App.reactivity.test.tsx` and `App.realtime.test.tsx`. Remove the `element` parameter in `App.stress.test.tsx`.
- **App.tsx (Reactivity)**: Refactor `fetchData` to not mutate the `loading` state internally. Wrap only the initial `fetchData` call inside `useEffect` with `setLoading`.
- **App.tsx (Data Fetching)**: Introduce a `prices` state. In `fetchData`, use `Promise.all` to fetch the latest trade price for each non-USD asset currently in the portfolio. Update the portfolio value calculation to use this `prices` map. Apply `.limit(100)` to the main `trades` query.

## 5. Verification Method
- **TypeScript Fixes**: Run `npm run build` in the `dashboard` directory. It should complete without `TS6133` errors.
- **Reactivity & Pagination Fixes**: Run `npm test` in the `dashboard` directory. Both `App.reactivity.test.tsx` and `App.pagination.test.tsx` should pass.
- **Manual Verification**: Run `npm run dev`, open the dashboard, and verify that the UI doesn't flash "Loading dashboard..." when new trades are inserted directly via the Supabase SQL editor. Verify that the total value calculates correctly even if the history array doesn't contain a specific asset's latest trade.
