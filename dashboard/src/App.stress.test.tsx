import { render, screen, waitFor } from '@testing-library/react';
import App from './App';
import { vi, describe, it, expect, beforeEach } from 'vitest';

// Generate mock data
function generateMockData() {
  const numTrades = 1000;
  const assets = ['AAPL', 'TSLA', 'MSFT', 'BTC', 'ETH'];
  const trades = [];
  
  for (let i = 0; i < numTrades; i++) {
    const asset = assets[Math.floor(Math.random() * assets.length)];
    // Make executed_at sequentially older
    const date = new Date(Date.now() - i * 1000).toISOString();
    trades.push({
      id: `trade_${i}`,
      asset_symbol: asset,
      trade_type: Math.random() > 0.5 ? 'BUY' : 'SELL',
      quantity: Math.random() * 10,
      price_usd: Math.random() * 1000 + 1,
      total_value_usd: 0, // Not used in calculation
      ai_justification: 'Random',
      executed_at: date
    });
  }

  // Generate portfolio
  const portfolio = [
    { asset_symbol: 'USD', balance: Math.random() * 100000 }
  ];
  assets.forEach(asset => {
    portfolio.push({
      asset_symbol: asset,
      balance: Math.random() * 100
    });
  });

  return { trades, portfolio };
}

let mockTrades: any[] = [];
let mockPortfolio: any[] = [];

vi.mock('./lib/supabase', () => {
  return {
    supabase: {
      from: vi.fn((table) => {
        const chain: any = {
          select: vi.fn(() => chain),
          eq: vi.fn((_column: string, value: string) => {
            chain._currentAsset = value;
            return chain;
          }),
          order: vi.fn(() => chain),
          limit: vi.fn(() => chain),
          maybeSingle: vi.fn(() => {
            if (table === 'trades') {
              const latest = mockTrades.find(t => t.asset_symbol === chain._currentAsset);
              return Promise.resolve({ data: latest || null, error: null });
            }
            return Promise.resolve({ data: null, error: null });
          }),
          then: function(resolve: any) {
            if (table === 'portfolio') {
              resolve({ data: mockPortfolio, error: null });
            } else if (table === 'trades') {
              resolve({ data: mockTrades, error: null });
            } else {
              resolve({ data: [], error: null });
            }
          }
        };
        return chain;
      }),
      channel: vi.fn(() => ({
        on: vi.fn().mockReturnThis(),
        subscribe: vi.fn()
      })),
      removeChannel: vi.fn()
    }
  };
});

describe('Dashboard Calculation Stress Test', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calculates portfolio value correctly with 1000 trades', async () => {
    const data = generateMockData();
    mockTrades = data.trades;
    mockPortfolio = data.portfolio;

    // Oracle Calculation
    let expectedTotal = mockPortfolio.find(p => p.asset_symbol === 'USD')?.balance || 0;
    
    data.portfolio.forEach(p => {
      if (p.asset_symbol === 'USD') return;
      const latestTrade = mockTrades.find(t => t.asset_symbol === p.asset_symbol);
      if (latestTrade) {
        expectedTotal += p.balance * latestTrade.price_usd;
      }
    });

    render(<App />);
    
    await waitFor(() => {
      expect(screen.queryByText('Loading dashboard...')).toBeNull();
    });

    const expectedString = expectedTotal.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    
    // Using a more flexible text matcher since it's rendered as $VALUE
    const totalValueElements = screen.getAllByText((content) => {
      return content.includes(expectedString) || content.replace(/[^0-9.-]+/g, "") === expectedTotal.toFixed(2);
    });
    
    let found = false;
    for (const el of totalValueElements) {
      if (el.textContent?.includes('$' + expectedString)) {
        found = true;
        break;
      }
    }
    expect(found).toBe(true);
  });

  it('handles missing trades for portfolio assets', async () => {
    mockTrades = [];
    mockPortfolio = [
      { asset_symbol: 'USD', balance: 50000 },
      { asset_symbol: 'AAPL', balance: 10 }
    ];

    render(<App />);
    
    await waitFor(() => {
      expect(screen.queryByText('Loading dashboard...')).toBeNull();
    });

    const expectedString = (50000).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    const totalValueElements = screen.getAllByText((content) => content.includes(expectedString));
    
    expect(totalValueElements.length).toBeGreaterThan(0);
  });

  it('handles precision floating point issues correctly', async () => {
    // 0.1 + 0.2 floating point precision test
    mockTrades = [
      { id: '1', asset_symbol: 'AAPL', price_usd: 0.1, executed_at: '2026-06-10T10:00:00Z', trade_type: 'BUY', quantity: 1, total_value_usd: 0.1, ai_justification: '' }
    ];
    mockPortfolio = [
      { asset_symbol: 'USD', balance: 0.2 },
      { asset_symbol: 'AAPL', balance: 1 } // 1 * 0.1 = 0.1, total = 0.3
    ];

    render(<App />);
    
    await waitFor(() => {
      expect(screen.queryByText('Loading dashboard...')).toBeNull();
    });

    const expectedString = (0.3).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    const totalValueElements = screen.getAllByText((content) => content.includes(expectedString));
    
    expect(totalValueElements.length).toBeGreaterThan(0);
  });
});
