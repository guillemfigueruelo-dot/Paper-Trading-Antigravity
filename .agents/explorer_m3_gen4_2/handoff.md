# Handoff Report

## Observation
- **Reactivity Flash**: `App.tsx:29` calls `setLoading(true)` inside `fetchData()`. `App.tsx:73-89` attach `fetchData` directly to Supabase realtime events.
- **Pagination / Truncation**: `App.tsx:47-50` fetches trades with `select('*')` which defaults to 1000 rows. `App.tsx:106` calculates asset value by searching this array: `trades.find((t) => t.asset_symbol === asset.asset_symbol)`.
- **Concurrency**: `App.tsx:73-89` subscribes to `portfolio` and `trades` channels separately. Both call `fetchData` immediately on change.
- **Performance/Scalability**: `App.tsx:105-110` loops `portfolio` and calls `trades.find()`, resulting in O(A × T) per render. `App.tsx:183-193` maps over the unbounded `trades` array directly to `<tr>` elements.

## Logic Chain
- **Reactivity Flash**: Every bot trade triggers a DB change -> `fetchData()` sets `loading=true` -> React unmounts the dashboard and renders the loading text -> fetch completes -> dashboard remounts.
- **Pagination / Truncation**: When a bot's trade for an asset exceeds 1000 rows in the past, it's missing from `trades`. The UI `find()` fails, and the portfolio logic defaults the asset's valuation to $0.
- **Concurrency**: A bot trade modifies both `trades` and `portfolio` simultaneously. Two realtime events fire at once, triggering two identical, overlapping `fetchData` requests.
- **Performance/Scalability**: The O(A × T) search on every render will cause stuttering. Rendering a huge amount of DOM nodes for historical trades will consume excess memory and crash the tab over time.

## Caveats
- I did not test the debounce function execution in a live environment.
- I assume a `.limit(50)` on the `trades` view is acceptable for the user. If the user strictly requires the full infinite list, virtualization (e.g. `react-window`) must be implemented instead.

## Conclusion
The root causes for all four issues are located within `dashboard/src/App.tsx`. 
The recommended fix strategy:
1. **Reactivity**: Remove `setLoading(true)` inside `fetchData`. Rely entirely on `useState(true)` for the initial load.
2. **Truncation**: Decouple asset pricing from the UI trade history. Fetch the latest price per asset explicitly using an O(A) query loop (e.g. `limit(1)` per asset), and store in a map.
3. **Concurrency**: Wrap the realtime callback in a debounce function (e.g. `setTimeout` of 300ms) to consolidate duplicate firing.
4. **Performance**: Constrain the trade history view by applying a `.limit(50)` to the `trades` Supabase query. Change the O(A × T) calculation to an O(A) lookup using the newly decoupled price map.

## Verification Method
- **Reactivity**: Add `console.log('Rendering loading')` on line 98. It should only fire once on initial mount, not when the DB updates.
- **Truncation/Performance**: Insert a dummy asset in `portfolio`, verify its value is calculated correctly via the new O(A) map lookup. Ensure the `trades` query includes `.limit(50)`. 
- **Concurrency**: Add a `console.log('Fetching')` in `fetchData`. Run a bot cycle and verify the console only logs the fetch once instead of twice.
