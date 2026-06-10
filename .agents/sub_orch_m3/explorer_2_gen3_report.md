# Dashboard Test Failure Analysis (Iteration 3)

## 1. Observation

When reviewing `dashboard/package.json`, there is no `test` script defined in the `"scripts"` block. 
Running `npx vitest run` in the `dashboard` directory fails with `ReferenceError: document is not defined`.
When running with the correct environment (`npx vitest run --environment jsdom`), the test suite fails at `src/App.test.tsx` with:
`TestingLibraryElementError: Unable to find an element with the text: (content, element) => content.includes("20.00% (Cash Only)").`
The test output DOM shows the "Performance vs Initial ($100k)" value is rendered as `95.00 %`.

## 2. Logic Chain

1. **Missing Test Script:** The user report identified a missing test script. `vitest` is installed as a dev dependency, but it's not wired into `npm run test`. Since the app uses React, `vitest` requires a DOM environment (like `jsdom`) to run correctly.
2. **Outdated Assertion:** In `App.test.tsx`, the mock data returns a USD balance of $120,000 and 1.5 BTC. It also mocks a trade history where the latest BTC trade price is $50,000. 
3. **New Calculation:** `App.tsx` was recently updated to calculate performance based on `totalPortfolioValue` (USD + Assets) rather than just USD (Cash Only). 
   - `totalPortfolioValue` = $120,000 (USD) + (1.5 BTC * $50,000/BTC) = $195,000.
   - Initial Capital = $100,000.
   - Performance = `((195,000 - 100,000) / 100,000) * 100` = `95.00%`.
4. Therefore, the assertion in `App.test.tsx` is looking for the old `20.00% (Cash Only)` string, which no longer exists and has been replaced by `95.00%`.

## 3. Caveats

- We are assuming `jsdom` is the intended test environment since it is already present in `devDependencies`.
- The exact format of the percentage in the DOM has a space (`95.00 %`), but `content.includes('95.00%')` might fail if there's whitespace inserted by React between elements. However, `.toFixed(2) + '%'` is used in the code (`{...toFixed(2)}%`), so `95.00%` will match correctly as a substring.

## 4. Conclusion & Recommended Fix Strategy

1. **Add Test Script in `package.json`**:
   Add a `test` script to `dashboard/package.json`. It must configure `jsdom` since `vite.config.ts` does not.
   ```json
   "scripts": {
     ...
     "test": "vitest run --environment jsdom"
   }
   ```
   *(Alternatively, add `test: { environment: 'jsdom' }` to `vite.config.ts` and set the script to `"test": "vitest run"`).*

2. **Update the Assertion in `App.test.tsx`**:
   Update lines 69-71 to look for the correct updated performance value, which is `95.00%`.
   - **Before:** `expect(screen.getByText((content, element) => content.includes('20.00% (Cash Only)'))).toBeTruthy();`
   - **After:** `expect(screen.getByText((content, element) => content.includes('95.00%'))).toBeTruthy();`
   Also, update the comment above the assertion to correctly describe the new calculation (`Initial is 100k, USD is 120k, BTC is 75k -> +95%`).

## 5. Verification Method

Once these fixes are implemented, the implementer can verify by running:
`npm run test` from the `dashboard` directory. The test `renders expected fields and performance calculation` should pass.
