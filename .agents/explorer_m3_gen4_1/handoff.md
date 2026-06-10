# Handoff Report: Milestone 3 Dashboard Investigation

## 1. Observation
- **Reactivity Flash**: `dashboard/src/App.tsx` calls `setLoading(true)` at line 29 inside `fetchData()`, which is triggered by Supabase background subscriptions (lines 78, 87). `App.tsx` lines 97-99 render `<div className="container">Loading dashboard...</div>` if `loading` is true.
- **Pagination / Truncation**: `App.tsx` lines 47-50 fetch trades via `supabase.from('trades').select('*')`, which has a default 1,000 row limit. Lines 105-110 compute `totalPortfolioValue` strictly by looking up the latest price via `trades.find(...)`. 
- **Concurrency**: `App.tsx` lines 73-89 register `fetchData` twice (to `portfolio-changes` and `trades-changes`). `PROJECT.md` indicates bot actions update both tables simultaneously.
- **Performance/Scalability**: `App.tsx` lines 105-110 iterate over `portfolio` and perform `trades.find(...)` inside the loop (O(A × T)). Lines 183-193 map the entire `trades` array into `<tr>` DOM elements.

## 2. Logic Chain
1. Any database event causes `fetchData` to run, which sets `loading=true`, unmounting the main UI and causing a flash.
2. Because the `trades` array is capped at 1,000, older assets aren't found by `trades.find()`. Thus, their price evaluates to $0, throwing off the portfolio value.
3. Since one bot transaction modifies two tables simultaneously, both DB events fire at the same time, invoking `fetchData` twice in parallel due to the lack of debouncing.
4. The `trades.find()` inside `portfolio.forEach()` causes O(A × T) processing per render. Rendering 1,000+ unfiltered rows to the DOM creates performance bottlenecks and potential crashes.

## 3. Caveats
- I did not investigate potential backend solutions (e.g., modifying the bot to save `current_price` directly in the `portfolio` table) as my scope is restricted to investigating the React/Vite Dashboard. My recommended strategies are focused heavily on frontend mitigations.
- I assumed the default Supabase REST limit is exactly 1,000 rows as per standard configuration, which aligns with the observed truncation bug.

## 4. Conclusion
The four bugs stem directly from `App.tsx`. 
To fix them:
- **Flash**: Pass a flag to `fetchData` to bypass `setLoading(true)` during background refreshes.
- **Truncation**: Stop relying on the `trades` history array for asset valuation; fetch latest prices explicitly for held assets or use a DB View.
- **Concurrency**: Apply a debounce function to the subscription callback.
- **Scalability**: Pre-compute a price map in O(T) for O(1) lookups in the portfolio loop, and apply standard UI pagination or virtualization for the history table.

## 5. Verification Method
- **Flash**: Modify DB manually; observe if UI flashes to a loading screen.
- **Truncation**: Insert a holding in `portfolio`, ensure its latest trade in `trades` is older than 1,000 rows, and verify `totalPortfolioValue` does not drop its value.
- **Concurrency**: Check network tab while simulating a bot trade; verify only one API fetch happens, not two.
- **Scalability**: Profile React rendering performance; verify DOM node count remains stable regardless of total trade count.
