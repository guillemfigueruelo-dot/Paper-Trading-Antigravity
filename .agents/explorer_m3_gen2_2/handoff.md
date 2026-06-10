# Handoff Report: Dashboard Fix Strategy

## Observation
1. **Performance Calculation Issue**: In `/dashboard/src/App.tsx` at lines 113-116, the performance calculation relies solely on `usdBalance`:
```tsx
            <h2>Performance vs Initial ($100k)</h2>
            <p className="big-number" style={{ color: usdBalance >= INITIAL_CAPITAL ? 'green' : 'red' }}>
              {(((usdBalance - INITIAL_CAPITAL) / INITIAL_CAPITAL) * 100).toFixed(2)}% (Cash Only)
            </p>
```
2. **String-to-Float Crash**: At line 136, `toFixed(8)` is called directly on `asset.balance`:
```tsx
                    <td>{asset.balance.toFixed(8)}</td>
```
If Supabase returns the NUMERIC type as a string, this throws a runtime error. `usdBalance` is also directly set to `usd.balance` at line 39.
3. **Trade Ordering**: At lines 43-46, trades are already fetched ordered by `executed_at` descending:
```tsx
        const { data: tradesData, error: tradesError } = await supabase
          .from('trades')
          .select('*')
          .order('executed_at', { ascending: false });
```

## Logic Chain
1. **Fixing String-to-Float**: Because the Supabase client may return numeric columns as strings, we must explicitly parse them before setting our React state. Applying `Number()` or `parseFloat()` when setting `usdBalance` and mapping the `portfolio` array ensures that `balance` is always a float, preventing the `toFixed()` crash.
2. **Fixing Performance Calculation**: Since `trades` is sorted by execution time descending, `trades.find(t => t.asset_symbol === asset.asset_symbol)` safely yields the most recent trade (and thus the most recent price) for any given asset.
3. We can calculate `assetsValue` by reducing the `portfolio` array, multiplying each `asset.balance` by its corresponding latest `price_usd` from `trades`. 
4. The total portfolio value is `usdBalance + assetsValue`. We then update the performance logic to `(((totalPortfolioValue - INITIAL_CAPITAL) / INITIAL_CAPITAL) * 100).toFixed(2)` to properly reflect the retained value of bought assets.

## Caveats
- Using the last trade price assumes there is at least one trade for every held asset. If an asset is somehow deposited without a corresponding trade entry, its `price_usd` won't be found and its value will default to $0. Given this is a paper trading app, this assumption is acceptable.

## Conclusion
Implement the following changes in `App.tsx`:
1. Parse the balances to numbers when setting state:
```typescript
const usdBal = usd ? parseFloat(usd.balance as any) : 0;
setUsdBalance(usdBal);
setPortfolio(portfolioData.filter((p) => p.asset_symbol !== 'USD').map(p => ({
  ...p,
  balance: parseFloat(p.balance as any)
})));
```
2. Compute `totalPortfolioValue` using the latest trade price:
```typescript
const assetsValue = portfolio.reduce((total, asset) => {
  const latestTrade = trades.find(t => t.asset_symbol === asset.asset_symbol);
  const currentPrice = latestTrade ? latestTrade.price_usd : 0;
  return total + (asset.balance * currentPrice);
}, 0);
const totalPortfolioValue = usdBalance + assetsValue;
```
3. Update the JSX to use `totalPortfolioValue` instead of `usdBalance` for the performance percentage.

## Verification Method
1. The implementer should apply the changes to `App.tsx`.
2. Run `npm run build` in `/dashboard` to verify there are no TypeScript or build errors.
3. Test locally or review the rendered components to confirm `asset.balance` renders without crashing and performance includes non-USD assets.
