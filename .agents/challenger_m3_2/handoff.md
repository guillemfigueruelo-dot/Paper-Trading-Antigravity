# Challenge Report: Milestone 3

## 1. Observation
- The Vite app builds successfully via `npm run build` (output: `✓ built in 210ms`).
- GitHub Pages configuration is present (`base: './'` in `vite.config.ts`).
- The components correctly render the expected fields. In `App.tsx:171`, it renders: `<td className="justification">{trade.ai_justification || 'N/A'}</td>`.
- The performance calculation at `App.tsx:115` is: `{(((usdBalance - INITIAL_CAPITAL) / INITIAL_CAPITAL) * 100).toFixed(2)}% (Cash Only)`. It completely ignores non-USD assets.
- I executed an empirical test (`test_performance.js`) which demonstrates the flaw: if the AI starts with $100,000 USD and successfully buys 1 BTC for $60,000, `usdBalance` becomes $40,000. The calculation evaluates to `-60.00%`.

## 2. Logic Chain
1. The user requested to verify that "performance calculation makes sense."
2. The core purpose of the dashboard is to track the performance of an AI paper trading bot.
3. Purchasing an asset exchanges cash for an asset of equivalent value, which should not immediately impact overall portfolio performance.
4. Because the calculation exclusively tracks `usdBalance` against `INITIAL_CAPITAL`, any capital deployed into assets is mathematically treated as a 100% loss of that capital.
5. Consequently, the dashboard will report massive negative performance figures whenever the AI successfully executes buy trades, rendering the metric useless and highly misleading.

## 3. Caveats
- The developer did include a `(Cash Only)` label and a comment acknowledging this is "naive" because live prices aren't available. However, a paper trading system could approximate portfolio value using the last traded price or purchase price rather than assuming held assets have zero value.
- There is a potential unverified runtime vulnerability in `App.tsx:136`: `asset.balance.toFixed(8)`. If Supabase returns the `numeric` field as a string (which PostgREST does for arbitrary precision numbers), calling `.toFixed()` will crash the React app. I was unable to definitively verify the PostgREST type return in this environment, but it remains a risk.

## 4. Conclusion
**Verdict: FAIL**

The Vite app builds correctly and displays all required fields (including `ai_justification`), but the performance calculation logic is fundamentally broken for a trading context. A trading dashboard cannot treat bought assets as a total loss of value. The logic needs to incorporate the value of held assets (e.g., based on purchase price or a price feed) to satisfy the requirement that the calculation makes sense.

## 5. Verification Method
1. Inspect `src/App.tsx` lines 90-116 to see the calculation logic.
2. Run the empirical test: `node ".agents/challenger_m3_2/test_performance.js"`. The output shows: `Bug reproduced: Performance does not account for asset value. Actual: -60.00 Expected: 0.00`.
