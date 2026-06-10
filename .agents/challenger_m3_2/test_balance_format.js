const assert = require('assert');

// Mock data as it might come from Supabase (where numeric without scale is returned as string)
const portfolioAsset = {
  asset_symbol: 'BTC',
  balance: '1.5' // string representation of numeric
};

try {
  // Simulating the UI rendering logic:
  // <td>{asset.balance.toFixed(8)}</td>
  const formattedBalance = portfolioAsset.balance.toFixed(8);
  console.log("Success:", formattedBalance);
} catch (e) {
  console.error("Bug reproduced: Crash when balance is a string.");
  console.error(e.message);
}
