# Observation
1. In `/dashboard/src/App.tsx`, the application currently calculates performance based strictly on cash. Lines 114-116 compute the performance percentage using `(((usdBalance - INITIAL_CAPITAL) / INITIAL_CAPITAL) * 100).toFixed(2)`, ignoring non-USD assets.
2. In `/dashboard/src/App.tsx`, line 136 directly invokes `.toFixed(8)` on `asset.balance`: `<td>{asset.balance.toFixed(8)}</td>`. If Supabase returns the `balance` field as a string (which is common for Postgres `numeric` or `decimal` types), this triggers a `TypeError: asset.balance.toFixed is not a function`, causing a React crash.
3. Lines 169-170 also invoke `.toFixed(2)` on `trade.price_usd` and `trade.total_value_usd`, which are similarly at risk of crashing.

# Logic Chain
1. To accurately reflect performance, the application must account for the value of held assets. Because the frontend does not have real-time market data APIs connected, it can approximate the current asset price by finding the most recent trade for each asset in the `trades` array.
2. The `trades` array is already fetched and sorted by `executed_at` descending (lines 43-46). Calling `trades.find((t) => t.asset_symbol === asset.asset_symbol)` will yield the most recent trade for an asset.
3. The total portfolio value can be calculated by summing `Number(usdBalance)` and `Number(asset.balance) * Number(latestTrade.price_usd)` for all held assets.
4. Using this `totalPortfolioValue` in place of `usdBalance` for the performance percentage formula `((totalPortfolioValue - INITIAL_CAPITAL) / INITIAL_CAPITAL) * 100` solves the logical bug where bought assets are treated as a 100% loss.
5. Wrapping all numeric database fields in `Number(...)` before calling `.toFixed()` guarantees a number type at runtime, preventing the React crash.

# Caveats
- Using the last traded price is an approximation for current market value. Since this is a paper trading context that only queries its own database, it may lag behind real external market data if no recent trades occurred. However, it's the most robust internally available metric.

# Conclusion
1. Create a derived variable `totalPortfolioValue` in `App.tsx` that computes `Number(usdBalance) + sum(Number(asset.balance) * last_traded_price)`.
2. Replace `usdBalance` with `totalPortfolioValue` in the performance calculation UI.
3. Add `Number()` casting around `usd.balance`, `asset.balance`, `trade.price_usd`, and `trade.total_value_usd` before performing arithmetic or `.toFixed()` formatting.

# Verification Method
1. The implementer should apply the changes to `/dashboard/src/App.tsx`.
2. Run `npm run build` in `/dashboard` to ensure there are no TypeScript compilation errors.
3. To confirm the runtime fix, you can temporarily mock a response where `balance` is a string (e.g., `"1.5"`) and verify the app renders without crashing.
4. Confirm visually that "Performance vs Initial" incorporates the approximate value of non-USD holdings instead of dropping immediately upon asset purchase.
