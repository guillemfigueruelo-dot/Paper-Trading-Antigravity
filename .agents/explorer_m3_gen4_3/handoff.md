# Handoff Report

## Observation
- **Reactivity Flash**: `App.tsx:29` calls `setLoading(true)` inside `fetchData()`, which is used as the un-parameterized callback for Supabase `postgres_changes` subscriptions (`App.tsx:78`, `App.tsx:87`). This triggers the loading screen (`App.tsx:97-99`) on every DB change.
- **Pagination / Truncation**: `App.tsx:49` uses `supabase.from('trades').select('*')`, which enforces a 1000-row limit. `App.tsx:105-110` calculates `totalPortfolioValue` using `trades.find()`. If an asset's last trade is older than 1000 rows, it will not be found, and its value will be ignored.
- **Concurrency**: Two separate channel subscriptions (`portfolio-changes` and `trades-changes`) call `fetchData` instantly. A single trade action modifies both tables, resulting in two concurrent, duplicate calls to `fetchData`.
- **Performance/Scalability**: `App.tsx:105-110` uses an O(A × T) loop per render cycle (`trades.find` inside `portfolio.forEach`). `App.tsx:183-193` maps the entire `trades` array directly into DOM `<tr>` elements without virtualization or limits.

## Logic Chain
1. Passing `fetchData` directly to real-time listeners means any background update triggers the same loading state as the initial page load, causing flashes.
2. Relying on the `trades` array for pricing is flawed because Supabase truncates results at 1000 rows; older assets "disappear" from the pricing history.
3. Because both `portfolio` and `trades` tables are updated during a single bot action, listening to both without debouncing triggers duplicate queries.
4. An unbounded `trades` array causes DOM performance degradation when mapped directly, and `trades.find()` inside `portfolio.forEach()` blocks the main thread with O(A × T) complexity on every React render.

## Caveats
- No caveats. The exact required changes are well scoped within the React client application and database queries.
- We assume `lodash.debounce` or similar is acceptable for concurrency, or we can build a custom hook. 
- We assume explicit fetching of latest prices (e.g. parallel `.limit(1)` queries) is preferable over writing new Postgres RPC functions to minimize backend changes.

## Conclusion
The dashboard requires four specific refactors in `App.tsx`:
1. Add an `isBackground` flag to `fetchData` to skip `setLoading(true)` on subscription events.
2. Decouple asset pricing from the `trades` array by explicitly fetching the latest price per held asset, or by creating an O(1) price map and ensuring all asset prices are loaded.
3. Wrap the real-time subscription callback in a debounce function to prevent duplicate network calls.
4. Introduce a `.limit(50)` on the `trades` query with pagination, and replace the O(A × T) `find()` inside `forEach()` with an O(1) map lookup (which is naturally resolved if strategy #2 is implemented).

## Verification Method
1. Start the React app and connect it to Supabase.
2. Simulate a bot trade (insert into `trades` and update `portfolio`). Observe that the screen does not flash (Fix 1), and network dev tools show only one debounced data fetch (Fix 3).
3. Add a test asset to the `portfolio` whose last `trade` is >1000 rows old. Verify that the portfolio value accurately reflects its current price (Fix 2).
4. Verify via React Profiler and DOM inspector that rendering is fast and only a limited number of trade rows (e.g., 50) are inserted into the DOM (Fix 4).
