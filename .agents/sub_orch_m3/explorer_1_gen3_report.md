# Observation
- In `c:/Users/Figue/Desktop/Paper Trading Antigravity/dashboard/src/App.test.tsx`, line 71 expects the text `20.00% (Cash Only)`.
- In `c:/Users/Figue/Desktop/Paper Trading Antigravity/dashboard/src/App.tsx`, lines 135-136 calculate performance as `{(((totalPortfolioValue - INITIAL_CAPITAL) / INITIAL_CAPITAL) * 100).toFixed(2)}%` without the " (Cash Only)" suffix.
- The `totalPortfolioValue` calculation in `App.tsx` now correctly includes both USD balance and asset values derived from the latest trade prices.
- In `App.test.tsx`, the mock data provides `120000` USD and `1.5` BTC. The mock trade provides a BTC price of `50000`. Thus, total portfolio value is `120000 + (1.5 * 50000) = 195000`. Performance is `((195000 - 100000) / 100000) * 100 = 95.00%`.
- In `c:/Users/Figue/Desktop/Paper Trading Antigravity/dashboard/package.json`, there is no `test` script in the `"scripts"` block, although `vitest` is installed in `"devDependencies"`.

# Logic Chain
1. The failure report identifies two specific issues: `App.test.tsx` expects an outdated performance calculation, and `package.json` is missing a `test` script.
2. The UI code in `App.tsx` no longer appends " (Cash Only)" to the performance string, and it calculates total value by factoring in both cash and asset holdings.
3. Based on the test's mock data (USD balance of $120k, 1.5 BTC at $50k/each), the total value is $195k. The performance versus the $100k initial capital is exactly +95.00%.
4. `App.test.tsx` currently asserts `20.00% (Cash Only)`, which fails because it evaluates against the old logic (only considering the $120k USD) and the old string format.
5. Updating the assertion in `App.test.tsx` to expect `95.00%` will accurately reflect the updated `App.tsx` logic.
6. Adding `"test": "vitest run"` to `package.json` will resolve the missing test script issue, allowing CI/CD to run tests in non-watch mode.

# Caveats
- Assuming `vitest run` is the desired command to execute tests for CI (rather than `vitest`, which defaults to watch mode).
- I did not verify whether any other parts of the application require tests, only investigating the specific failures reported from Iteration 2.

# Conclusion
The test suite fails because `App.test.tsx` asserts an outdated string format and calculation for portfolio performance, and there is no NPM test script defined. 

**Fix Strategy**:
1. In `dashboard/package.json`, add `"test": "vitest run"` to the `"scripts"` object.
2. In `dashboard/src/App.test.tsx`, update lines 70-71 to reflect the new total portfolio calculation:
```typescript
    // Initial is 100k, USD is 120k, BTC is 1.5 * 50k = 75k -> Total 195k -> +95%
    expect(screen.getByText((content, element) => content.includes('95.00%'))).toBeTruthy();
```

# Verification Method
1. Implement the changes to `App.test.tsx` and `package.json`.
2. Change directory to `c:/Users/Figue/Desktop/Paper Trading Antigravity/dashboard`.
3. Run `npm test` (or the package manager equivalent).
4. The test suite should pass successfully.
