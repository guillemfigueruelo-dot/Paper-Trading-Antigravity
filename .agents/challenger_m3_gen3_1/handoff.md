# Handoff Report

## 1. Observation
- The dashboard calculates total value using: `const latestTrade = trades.find((t) => t.asset_symbol === asset.asset_symbol);` on the local `trades` array.
- The `trades` array is populated by `supabase.from('trades').select('*').order('executed_at', { ascending: false });`. There is no `.limit()` or pagination handling, meaning it falls back to the database's `max-rows` default (usually 1000).
- The dashboard listens to real-time events on both `portfolio` and `trades` tables, triggering `fetchData()` on each event.
- `fetchData()` unconditionally calls `setLoading(true)`, and the component unmounts the entire UI with `if (loading) return <div>Loading dashboard...</div>;`.
- I wrote `App.pagination.test.tsx` and `App.reactivity.test.tsx` to verify these behaviors. Running `npm test` fails both tests.

## 2. Logic Chain
- Because Supabase truncates results at `max-rows` by default, an asset whose last trade is older than the `max-rows` window will not be present in the `trades` array.
- When `trades.find()` fails to find the asset, it returns `undefined`, which skips the value addition (`totalPortfolioValue += asset.balance * latestTrade.price_usd`). This values the asset at $0, corrupting the dashboard metrics.
- Because `setLoading(true)` is called on every background refresh, and because a single bot action triggers two simultaneous background refreshes (due to updating both `portfolio` and `trades`), the dashboard flashes a white loading screen twice for every trade, rendering it visually unusable under active trading.

## 3. Caveats
- Supabase's `max-rows` limit can theoretically be configured higher, but this would still fetch the entire trade history on every page load and realtime update, leading to severe performance degradation. Pagination or an RPC approach is required.

## 4. Conclusion
- **VERDICT: FAIL**. The dashboard logic is mathematically correct for small, static datasets but functionally broken under realistic load. The pagination limitation corrupts financial calculations, and the reactivity implementation destroys the user experience (flashing UI).

## 5. Verification Method
- **Run tests**: Navigate to `dashboard` and run `npm test`. Observe that `App.pagination.test.tsx` and `App.reactivity.test.tsx` fail.
- **Source verification**: Inspect `App.tsx` lines ~29 and ~97 for the `setLoading(true)` unmount bug. Inspect lines ~47 and ~106 for the un-paginated `select('*')` and `trades.find()` logic.
