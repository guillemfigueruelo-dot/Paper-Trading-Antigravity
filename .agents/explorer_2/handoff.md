# Handoff Report

## 1. Observation
- `dashboard/package.json` has no `test` script.
- Running tests requires a jsdom environment (`document is not defined` error if run plainly).
- With `jsdom`, `App.test.tsx` fails because it asserts `20.00% (Cash Only)`, but the new `App.tsx` calculates performance using both cash ($120,000) and assets (1.5 BTC @ $50,000 = $75,000).

## 2. Logic Chain
- Total value = $120k + $75k = $195k. 
- Initial capital = $100k. 
- Growth = ($195k - $100k) / $100k = +95%.
- Therefore, the UI renders `95.00%`. The test must be updated to expect `95.00%` instead of `20.00% (Cash Only)`.
- The `package.json` must have `"test": "vitest run --environment jsdom"`.

## 3. Caveats
- Assuming `jsdom` is the required environment, since it's already in `devDependencies`. The fix could alternatively modify `vite.config.ts`.

## 4. Conclusion
The implementer needs to:
1. Update `package.json` to add `"test": "vitest run --environment jsdom"`.
2. Update `App.test.tsx` assertion to expect `95.00%` instead of `20.00% (Cash Only)`.

## 5. Verification Method
Run `npm run test` in the `dashboard` directory and confirm `renders expected fields and performance calculation` passes.
