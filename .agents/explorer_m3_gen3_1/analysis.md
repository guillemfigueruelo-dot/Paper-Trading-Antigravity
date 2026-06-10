# Analysis of Dashboard Test Failures

## 1. Missing Test Script
**Observation:**
In `c:/Users/Figue/Desktop/Paper Trading Antigravity/dashboard/package.json`, the `"scripts"` block is missing a `test` command.
```json
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "lint": "eslint .",
    "preview": "vite preview"
  }
```

**Logic:**
The test suite cannot run using `npm test` without a `test` script defined. Since the project uses Vitest (`vitest` is in `devDependencies`), a `test` script should be added.

## 2. Outdated Performance Assertion
**Observation:**
In `c:/Users/Figue/Desktop/Paper Trading Antigravity/dashboard/src/App.test.tsx`, lines 69-71 have an outdated assertion:
```typescript
    // Check Performance calculation
    // Initial is 100k, USD is 120k -> +20%
    expect(screen.getByText((content, element) => content.includes('20.00% (Cash Only)'))).toBeTruthy();
```

However, in `c:/Users/Figue/Desktop/Paper Trading Antigravity/dashboard/src/App.tsx`, lines 103-110, the total portfolio value is now calculated dynamically by multiplying the asset balance with the latest trade price:
```typescript
  // Calculate total portfolio value using the latest trade price for each asset
  let totalPortfolioValue = usdBalance;
  portfolio.forEach((asset) => {
    const latestTrade = trades.find((t) => t.asset_symbol === asset.asset_symbol);
    if (latestTrade) {
      totalPortfolioValue += asset.balance * latestTrade.price_usd;
    }
  });
```

And rendered without the `(Cash Only)` suffix at lines 134-136:
```typescript
            <p className="big-number" style={{ color: totalPortfolioValue >= INITIAL_CAPITAL ? 'green' : 'red' }}>
              {(((totalPortfolioValue - INITIAL_CAPITAL) / INITIAL_CAPITAL) * 100).toFixed(2)}%
            </p>
```

**Logic:**
Given the mock data in `App.test.tsx`:
- USD Balance: 120,000
- BTC Balance: 1.5
- BTC Latest Price: 50,000
Total Value = 120,000 + (1.5 * 50,000) = 195,000.
Performance = ((195,000 - 100,000) / 100,000) * 100 = 95.00%.

The test currently expects `20.00% (Cash Only)`, but the actual rendered string is `95.00%`.

## 3. Recommended Fix Strategy
1. **Update `package.json`**: Add `"test": "vitest run"` (or `"vitest"`) to the `"scripts"` section.
2. **Update `App.test.tsx`**: Change the assertion on line 71 to expect `95.00%` instead of `20.00% (Cash Only)`. Also, update the corresponding comments to reflect the new 95% calculation.
