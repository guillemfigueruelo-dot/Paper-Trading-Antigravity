# Investigation Analysis: Dashboard Test Failure

## Overview
Iteration 2 failed because `App.test.tsx` expects an outdated performance metric calculation, and the project lacks a `test` script in `package.json` to execute the tests.

## 1. Missing 'test' script in `package.json`
**Observation**:
In `c:/Users/Figue/Desktop/Paper Trading Antigravity/dashboard/package.json` (lines 6-11), the `scripts` block defines `dev`, `build`, `lint`, and `preview`, but lacks a `test` script. However, testing dependencies (`vitest`, `@testing-library/react`, etc.) are present in `devDependencies`.

**Fix Strategy**:
Add `"test": "vitest run"` to the `scripts` object in `package.json`. The `run` flag ensures it executes once and exits, which is required for CI/automation instead of entering watch mode.

## 2. Outdated Performance Assertion in `App.test.tsx`
**Observation**:
In `c:/Users/Figue/Desktop/Paper Trading Antigravity/dashboard/src/App.test.tsx` (lines 69-71), the test asserts:
```typescript
// Initial is 100k, USD is 120k -> +20%
expect(screen.getByText((content, element) => content.includes('20.00% (Cash Only)'))).toBeTruthy();
```

However, in `c:/Users/Figue/Desktop/Paper Trading Antigravity/dashboard/src/App.tsx` (lines 101-110), the application logic has been updated to calculate `totalPortfolioValue` by adding `usdBalance` to the current value of held assets (based on their latest trade price):
```typescript
let totalPortfolioValue = usdBalance;
portfolio.forEach((asset) => {
  const latestTrade = trades.find((t) => t.asset_symbol === asset.asset_symbol);
  if (latestTrade) {
    totalPortfolioValue += asset.balance * latestTrade.price_usd;
  }
});
```

The string `(Cash Only)` has also been removed from the rendering logic in `App.tsx` (line 135).

**Logic Chain**:
Based on the mock data provided in `App.test.tsx` (lines 16-40):
1. `usdBalance` = 120,000
2. `BTC` balance = 1.5
3. Latest `BTC` trade price = 50,000
4. `totalPortfolioValue` = 120,000 + (1.5 * 50,000) = 195,000
5. `INITIAL_CAPITAL` = 100,000
6. Performance % = `((195,000 - 100,000) / 100,000) * 100` = **95.00%**

**Fix Strategy**:
Update `App.test.tsx` line 71 to assert the correct updated performance value:
```typescript
// Initial is 100k, Portfolio is 195k (120k USD + 1.5 BTC @ 50k) -> +95%
expect(screen.getByText((content, element) => content.includes('95.00%'))).toBeTruthy();
```
