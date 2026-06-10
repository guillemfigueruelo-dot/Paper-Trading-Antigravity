const assert = require('assert');

// Mock state
const INITIAL_CAPITAL = 100000;
let usdBalance = 40000; // After buying 1 BTC for 60k
let portfolio = [{ asset_symbol: 'BTC', balance: 1 }];

// App logic for performance calculation
let performanceStr = (((usdBalance - INITIAL_CAPITAL) / INITIAL_CAPITAL) * 100).toFixed(2);

console.log("Performance calculated as:", performanceStr + "%");

// We assert that the performance should be 0% if the asset value is included, 
// but the current logic evaluates to -60.00%
try {
    assert.strictEqual(performanceStr, "0.00");
} catch (e) {
    console.error("Bug reproduced: Performance does not account for asset value. Actual:", performanceStr, "Expected: 0.00");
}
