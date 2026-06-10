import { render, screen, waitFor } from '@testing-library/react';
import App from './App';
import { vi, describe, it, expect, beforeEach } from 'vitest';

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
              resolve({ data: mockTrades.slice(0, 100), error: null });
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

describe('Dashboard Pagination Stress Test', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calculates portfolio value correctly even if asset latest trade is beyond pagination limit', async () => {
    mockTrades = [];
    // Generate 1000 trades of AAPL
    for (let i = 0; i < 1000; i++) {
      mockTrades.push({
        id: `trade_${i}`,
        asset_symbol: 'AAPL',
        trade_type: 'BUY',
        quantity: 1,
        price_usd: 150,
        total_value_usd: 150,
        ai_justification: 'Random',
        executed_at: new Date(Date.now() - i * 1000).toISOString()
      });
    }
    // Add one trade of BTC that is older than 1000 AAPL trades
    mockTrades.push({
      id: `trade_btc`,
      asset_symbol: 'BTC',
      trade_type: 'BUY',
      quantity: 1,
      price_usd: 50000,
      total_value_usd: 50000,
      ai_justification: 'Random',
      executed_at: new Date(Date.now() - 2000000).toISOString()
    });

    // Mock portfolio has AAPL and BTC
    mockPortfolio = [
      { asset_symbol: 'USD', balance: 0 },
      { asset_symbol: 'AAPL', balance: 10 },  // 10 * 150 = 1500
      { asset_symbol: 'BTC', balance: 1 }     // 1 * 50000 = 50000
    ];

    // Oracle expects total to be 51500
    const expectedTotal = 51500;

    render(<App />);
    
    await waitFor(() => {
      expect(screen.queryByText('Loading dashboard...')).toBeNull();
    });

    const expectedString = expectedTotal.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    
    const totalValueElements = screen.queryAllByText((content) => content.includes(expectedString));
    
    expect(totalValueElements.length).toBeGreaterThan(0); // It should find the correct total!
  });
});
