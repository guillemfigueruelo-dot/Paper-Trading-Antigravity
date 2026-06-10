## Challenge Summary

**Overall risk assessment**: CRITICAL

The current dashboard calculation logic for total portfolio value and rendering has critical flaws in performance, scalability, and correctness. It assumes a small, bounded number of trades. In a real-world bot scenario, trades will grow unbounded, leading to UI crashes, incorrect portfolio valuation, and severe performance degradation.

## Challenges

### [Critical] Challenge 1: Lack of Pagination / Virtualization on Trades Rendering

- **Assumption challenged**: The browser can render the entire trade history in a single HTML table.
- **Attack scenario**: The trading bot executes several trades a day. After a few months, the `trades` table contains 10,000+ rows. 
- **Blast radius**: `supabase.from('trades').select('*')` (if unbounded) will pull a massive JSON payload, and React will attempt to render 10,000+ `<tr>` elements into the DOM. This will cause the browser tab to freeze, crash with an Out-of-Memory (OOM) error, or severely degrade user experience.
- **Mitigation**: Implement pagination via Supabase `.range(0, 50)` or infinite scrolling with a virtualized list (e.g., `react-window`).

### [Critical] Challenge 2: Portfolio Valuation Corrupted by Data Truncation

- **Assumption challenged**: All trades are available in the client memory, so `trades.find()` will always find a price for held assets.
- **Attack scenario**: Supabase's PostgREST API imposes a default response limit (often 1000 rows). If a user holds an asset (e.g., TSLA) but the bot has made 1000 trades on other assets since TSLA was last traded, the `trades` array will not contain any TSLA trades.
- **Blast radius**: The `latestTrade` will be `undefined`. The calculation `totalPortfolioValue += asset.balance * latestTrade.price_usd` will simply skip that asset or add 0. The total portfolio value and performance percentage will drop drastically, showing a completely incorrect dashboard.
- **Mitigation**: Store current market prices separately (e.g., in a `market_data` table or via real-time API fetch) rather than relying on historical trade execution prices. If relying on trades, do a specific Supabase query to get the latest trade per asset rather than a client-side `.find()` over a truncated array.

### [High] Challenge 3: O(A × T) Complexity in Render Cycle

- **Assumption challenged**: Scanning the trades array for each asset is performant.
- **Attack scenario**: Suppose the client fetches $T$ trades and holds $A$ assets. During every render cycle, `portfolio.forEach` executes `trades.find(...)`. If an asset has no trades in the array, `.find()` iterates through all $T$ items. This results in $O(A \times T)$ complexity on the UI thread.
- **Blast radius**: For 50 assets and 10,000 trades, this is 500,000 iterations per render cycle. Since this happens synchronously in the React render phase, it blocks the main thread, causing UI jank and unresponsiveness.
- **Stress Test Result**: A Node.js simulation in `stress.js` with 100 assets and 100,000 trades took ~130ms just for the math operation, which is over the 16ms budget for a 60fps frame, causing noticeable lag.
- **Mitigation**: Build a $O(1)$ lookup map (`Record<string, number>`) of the latest prices in a `useMemo` hook, reducing complexity to $O(T + A)$.

## Stress Test Results

- **Scenario**: 100 assets, 100,000 trades (last asset traded frequently, others rarely).
- **Expected behavior**: Fast valuation ($< 1ms$), correct portfolio value.
- **Actual/Predicted behavior**: Takes ~130ms to calculate. If the array is truncated to 1000 items (simulating Supabase limit), the value calculation drops from 51,500 to 2,000 because older assets are omitted.
- **Result**: **FAIL**. 

## Unchallenged Areas

- **Real-time subscriptions (`supabase.channel`)**: Not challenged for memory leaks under high trade volume, though the `fetchData` function is repeatedly called on every single change, causing full re-fetches and $O(A \times T)$ recalculations per event instead of incremental updates.
