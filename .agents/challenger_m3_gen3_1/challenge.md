# Dashboard Logic Challenge Report

## Challenge Summary

**Overall risk assessment**: HIGH

The dashboard suffers from three distinct bugs regarding data reactivity, API constraints, and concurrency. While basic calculations are mathematically correct for small, static datasets, the dashboard will fail severely under realistic paper-trading conditions over time.

## Challenges

### [Critical] Challenge 1: The Pagination / Truncation Bug
- **Assumption challenged**: The client assumes that `supabase.from('trades').select('*')` returns the *entire* history of trades unconditionally, and therefore `trades.find()` will always find an asset's last execution price.
- **Attack scenario**: Supabase's `select('*')` API defaults to a `max-rows` limit (typically 1000 rows). If the bot executes 1000 trades in highly volatile assets (e.g., AAPL), an older asset in the portfolio (e.g., BTC) that hasn't been traded recently gets pushed beyond the 1000-row window.
- **Blast radius**: `trades.find()` returns `undefined` for older assets. The dashboard defaults the value of these assets to $0. The Total Portfolio Value and Performance metrics become corrupted and artificially lower.
- **Mitigation**: Fetch the *latest trade per asset* via an RPC call, or apply pagination, or use a distinct `market_prices` table.
- **Test reference**: See `App.pagination.test.tsx`

### [High] Challenge 2: The Reactivity Flash Bug (Liveness)
- **Assumption challenged**: The client assumes fetching data takes negligible time and the user doesn't mind a loading state during background updates.
- **Attack scenario**: The bot makes a trade, triggering a realtime update on the Supabase channel. `fetchData()` is called, which unconditionally calls `setLoading(true)`. 
- **Blast radius**: Because `if (loading) return <div className="container">Loading dashboard...</div>;`, the entire dashboard unmounts and remounts as a white screen on *every single database update*. This makes the dashboard unusable during active trading periods.
- **Mitigation**: Introduce a separate `isRefreshing` state for background updates, preserving the previous data on screen, and only show the full loading screen on the initial load.
- **Test reference**: See `App.reactivity.test.tsx`

### [Medium] Challenge 3: Concurrent Fetch Duplication
- **Assumption challenged**: Realtime triggers should always trigger a full data fetch independently.
- **Attack scenario**: A trade involves updating the `portfolio` table AND inserting into the `trades` table simultaneously. The dashboard subscribes to both tables and triggers `fetchData` on both events.
- **Blast radius**: `fetchData` is executed twice concurrently. This wastes network resources, causes double-flashing, and introduces race conditions (the slower request overwrites the UI with potentially stale data if executed slightly out of order).
- **Mitigation**: Debounce the `fetchData` function or consolidate the realtime listeners.

## Stress Test Results

- **Reactivity Stress Test** → Dashboard should not unmount during realtime updates → `Loading dashboard...` flashes on screen → **FAIL**
- **Pagination Stress Test** → Assets traded >1000 rows ago should retain value → Asset valued at $0 due to missing trade → **FAIL**
- **1000 Trade Load Test** → Calculation mathematically correct → Value calculated successfully → **PASS**
- **Precision Floating Point Test** → `0.1 + 0.2` rounding → UI formats to `0.30` → **PASS**

## Unchallenged Areas

- **Supabase Authentication**: The dashboard relies on anon-key access, assuming RLS allows public reads. This was not challenged as it's an infrastructural configuration.
