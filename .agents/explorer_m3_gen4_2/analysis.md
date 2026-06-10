# Investigation Analysis: Dashboard Issues

## 1. Reactivity Flash
**Observation**: 
In `dashboard/src/App.tsx`, lines 28-68 define `fetchData()`, which explicitly calls `setLoading(true)` on line 29 before fetching data. Lines 73-89 attach `fetchData` directly to the Supabase `postgres_changes` events for both the `portfolio` and `trades` tables.
**Logic Chain**:
Because `fetchData` sets `loading` to `true` every time it runs, any background update from Supabase triggers this function, forcing `loading` to `true`. This causes the main component to return the loading screen (`if (loading) { return <div className="container">Loading dashboard...</div>; }` on lines 97-99), resulting in a jarring UI flash.
**Fix Strategy**: 
Remove `setLoading(true)` from the `fetchData` function. Since `loading` is initialized to `true` (`const [loading, setLoading] = useState(true);`), the initial render will naturally show the loading screen, and subsequent background fetches will silently update the state without unmounting the UI.

## 2. Pagination / Truncation
**Observation**: 
On line 47, trades are fetched via `supabase.from('trades').select('*').order(...)`, which defaults to a 1000-row limit in Supabase PostgREST. 
On lines 104-110, `totalPortfolioValue` is calculated by iterating over the `portfolio` and finding the latest price in the local `trades` array: `const latestTrade = trades.find((t) => t.asset_symbol === asset.asset_symbol);`.
**Logic Chain**:
If an asset was last traded more than 1000 trades ago, it will not appear in the fetched `trades` array. The `find()` call will return `undefined`, and the asset's value will be excluded from the `totalPortfolioValue` calculation, treating its holdings as worth $0.
**Fix Strategy**: 
Decouple the asset pricing logic from the trade history UI. Instead of relying on the UI `trades` array, fetch the latest price for each held asset explicitly. For example, by executing a specific query for the latest trade per asset: `Promise.all(portfolioData.map(asset => supabase.from('trades').select('price_usd').eq('asset_symbol', asset.asset_symbol).order('executed_at', { ascending: false }).limit(1).single()))`. Store this in a dedicated `assetPrices` dictionary state.

## 3. Concurrency
**Observation**:
Lines 73-94 create two separate Supabase subscriptions: one for `portfolio` changes and one for `trades` changes. Both directly trigger `fetchData`.
**Logic Chain**:
A standard bot transaction will insert a row into `trades` and update a row in `portfolio` almost simultaneously. This fires both event listeners concurrently, causing `fetchData` to be called twice in rapid succession, doubling the number of API requests to Supabase and risking race conditions.
**Fix Strategy**: 
Debounce the background refresh. Create a `debouncedFetchData` function using `setTimeout` (or a utility like Lodash `debounce`), and pass that to the event listeners. Alternatively, listen to the entire `public` schema (`{ event: '*', schema: 'public' }`) in a single channel and apply a debounce.

## 4. Performance/Scalability
**Observation**: 
- **O(A × T) Loop**: On lines 105-110, `portfolio.forEach()` runs `trades.find(...)` on every render.
- **DOM Crash**: On lines 182-194, `trades.map(...)` renders a table row for every fetched trade without any pagination or bounds.
**Logic Chain**:
React calls the render function frequently. `Array.find()` inside `Array.forEach()` results in an O(A × T) time complexity, which will block the main thread as `T` grows. Furthermore, rendering 1000 (or more) raw `<tr>` elements to the DOM consumes significant memory and layout computation, degrading browser performance.
**Fix Strategy**: 
- **O(A × T) Fix**: Fix Issue 2 by creating an `assetPrices` map object. The value calculation loop then becomes an O(A) operation by looking up `assetPrices[asset.asset_symbol]`.
- **DOM Crash Fix**: Limit the number of trades fetched for the UI history (e.g., append `.limit(50)` to the `trades` fetch query) since a dashboard generally only needs to display recent history. For a full history view, implement pagination or use a DOM virtualization library like `react-window`.
