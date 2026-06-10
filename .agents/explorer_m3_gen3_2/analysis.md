# Investigation Analysis: Dashboard Test Failure

## Overview
The Dashboard React/Vite app is failing in testing due to an outdated performance assertion in `App.test.tsx` and a missing `test` script in `package.json`.

## Evidence Chain

### 1. Missing test script in `package.json`
**Observation**: 
`c:/Users/Figue/Desktop/Paper Trading Antigravity/dashboard/package.json` lines 6-11 show the `scripts` object:
```json
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "lint": "eslint .",
    "preview": "vite preview"
  },
```
The `test` script is missing. However, `vitest` is installed as a devDependency (line 34: `"vitest": "^4.1.8"`).

**Conclusion for `package.json`**: 
Add `"test": "vitest"` or `"test": "vitest run"` to the `scripts` block.

### 2. Outdated Performance Assertion in `App.test.tsx`
**Observation**:
In `c:/Users/Figue/Desktop/Paper Trading Antigravity/dashboard/src/App.test.tsx` (lines 69-71), the test asserts the following for performance:
```tsx
    // Check Performance calculation
    // Initial is 100k, USD is 120k -> +20%
    expect(screen.getByText((content, element) => content.includes('20.00% (Cash Only)'))).toBeTruthy();
```

**Observation**:
In `c:/Users/Figue/Desktop/Paper Trading Antigravity/dashboard/src/App.tsx` (lines 101-110, 134-136), the performance calculation was updated to include the value of all assets (not just cash):
```tsx
  const INITIAL_CAPITAL = 100000;

  // Calculate total portfolio value using the latest trade price for each asset
  let totalPortfolioValue = usdBalance;
  portfolio.forEach((asset) => {
    const latestTrade = trades.find((t) => t.asset_symbol === asset.asset_symbol);
    if (latestTrade) {
      totalPortfolioValue += asset.balance * latestTrade.price_usd;
    }
  });
```
And it renders the value without the "(Cash Only)" suffix:
```tsx
            <p className="big-number" style={{ color: totalPortfolioValue >= INITIAL_CAPITAL ? 'green' : 'red' }}>
              {(((totalPortfolioValue - INITIAL_CAPITAL) / INITIAL_CAPITAL) * 100).toFixed(2)}%
            </p>
```

**Calculation with Test Mock Data**:
In `App.test.tsx`, the mock returns:
- `portfolio`: USD balance = 120,000, BTC balance = 1.5
- `trades`: latest BTC trade `price_usd` = 50,000
Total portfolio value = $120,000 (USD) + (1.5 * $50,000) (BTC) = $195,000.
Performance vs Initial ($100,000) = `(($195,000 - $100,000) / $100,000) * 100` = `95.00%`.

**Conclusion for `App.test.tsx`**: 
The assertion should be updated from `20.00% (Cash Only)` to `95.00%`.

## Proposed Fix Strategy

1. **In `dashboard/package.json`**:
   Add `"test": "vitest"` to the `"scripts"` object.

2. **In `dashboard/src/App.test.tsx`**:
   Update lines 69-71 to reflect the new total portfolio calculation.
   ```tsx
   // Initial is 100k, total value is 120k (USD) + 1.5 * 50k (BTC) = 195k -> +95%
   expect(screen.getByText((content, element) => content.includes('95.00%'))).toBeTruthy();
   ```
