// Stress test for dashboard calculation logic

const calculatePortfolioValue = (usdBalance, portfolio, trades) => {
  let totalPortfolioValue = usdBalance;
  portfolio.forEach((asset) => {
    const latestTrade = trades.find((t) => t.asset_symbol === asset.asset_symbol);
    if (latestTrade) {
      totalPortfolioValue += asset.balance * latestTrade.price_usd;
    }
  });
  return totalPortfolioValue;
};

// Scenario 1: Performance with many trades
const NUM_TRADES = 100000;
const NUM_ASSETS = 100;

const portfolio = [];
for (let i = 0; i < NUM_ASSETS; i++) {
  portfolio.push({ asset_symbol: `ASSET_${i}`, balance: 10 });
}

const trades = [];
for (let i = 0; i < NUM_TRADES; i++) {
  trades.push({
    asset_symbol: `ASSET_${NUM_ASSETS - 1}`, // only the last asset is traded frequently
    price_usd: 100
  });
}
// Add the other assets at the very end
for (let i = 0; i < NUM_ASSETS - 1; i++) {
  trades.push({
    asset_symbol: `ASSET_${i}`,
    price_usd: 50
  });
}

const start = performance.now();
const value = calculatePortfolioValue(1000, portfolio, trades);
const end = performance.now();

console.log(`Scenario 1 (O(A * T) Complexity):`);
console.log(`Calculated value: ${value}`);
console.log(`Time taken: ${(end - start).toFixed(2)} ms`);

// Scenario 2: Correctness when trades are capped (Supabase 1000 limit)
// If an asset hasn't been traded in the last 1000 trades, its value is 0.
const cappedTrades = trades.slice(0, 1000);
const cappedValue = calculatePortfolioValue(1000, portfolio, cappedTrades);

console.log(`\nScenario 2 (Supabase fetch limit 1000 rows):`);
console.log(`Calculated value with all trades: ${value}`);
console.log(`Calculated value with capped trades: ${cappedValue}`);
