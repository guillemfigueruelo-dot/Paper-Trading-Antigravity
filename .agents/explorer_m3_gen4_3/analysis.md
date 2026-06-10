# Analysis of Dashboard Issues

## 1. Reactivity Flash
**Observation**: In `App.tsx` (lines 27-90), `fetchData()` is called both on initial mount and as the callback for Supabase real-time subscriptions (`portfolio-changes` and `trades-changes`). On line 29, `fetchData` unconditionally calls `setLoading(true)`. The component renders `<div className="container">Loading dashboard...</div>;` when `loading` is true (lines 97-99), causing a UI flash on every background update.
**Fix Strategy**: Modify `fetchData` to accept a parameter (e.g., `isBackgroundUpdate = false`). If it's a background update, bypass `setLoading(true)`. Update the subscription callbacks to pass `true`.

## 2. Pagination / Truncation
**Observation**: At line 49, the query `supabase.from('trades').select('*').order('executed_at', { ascending: false })` relies on Supabase's default limit of 1000 rows. At lines 105-110, `totalPortfolioValue` is calculated by finding the latest price in the `trades` array for each asset in the `portfolio`. If an asset hasn't been traded recently (falls out of the top 1000 rows), `trades.find()` returns undefined, and the asset contributes $0 to the total value.
**Fix Strategy**: Decouple price lookup from the `trades` history fetch. Instead of scanning the history, explicitly fetch the latest price for each held asset (e.g., executing `supabase.from('trades').select('price_usd').eq('asset_symbol', asset.asset_symbol).order('executed_at', { ascending: false }).limit(1)` in parallel for all portfolio assets) or create a database view/RPC that returns current prices. 

## 3. Concurrency
**Observation**: Lines 73-90 set up two separate Supabase subscriptions—one for `portfolio` and one for `trades`—both triggering the exact same `fetchData` function. Since a single paper trade execution inserts into `trades` and updates `portfolio`, both channels fire simultaneously, causing two concurrent, duplicate `fetchData` executions and API calls.
**Fix Strategy**: Implement a debounce mechanism for the background fetch. Wrap `fetchData` in a debounce function (e.g., `lodash.debounce` or a custom `setTimeout` implementation with a ~300ms delay) so that multiple rapid database events are coalesced into a single fetch.

## 4. Performance/Scalability
**Observation**: 
- **O(A × T) Loop**: Lines 105-110 use `trades.find()` inside `portfolio.forEach()`, running on every render cycle. As `trades` grows, this blocks the main thread.
- **Unbounded DOM**: Lines 183-193 map over the entire `trades` array to render table rows without virtualization or pagination.
**Fix Strategy**: 
- For the loop: Compute an asset-to-price map once (or use the dedicated price fetch mentioned in strategy #2) to replace the O(A × T) nested lookup with an O(1) map lookup.
- For the DOM: Add `.limit(50)` to the `trades` query and implement simple server-side pagination (Next/Prev buttons), OR implement list virtualization using a library like `@tanstack/react-virtual` to only render rows visible in the viewport.
