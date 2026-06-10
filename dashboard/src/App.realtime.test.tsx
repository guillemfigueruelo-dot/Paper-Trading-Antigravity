import { render, screen, waitFor, act } from '@testing-library/react';
import App from './App';
import { vi, describe, it, expect, beforeEach } from 'vitest';

let mockTrades: any[] = [];
let mockPortfolio: any[] = [];
let portfolioCallback: any = null;

vi.mock('./lib/supabase', () => {
  return {
    supabase: {
      from: vi.fn((table) => {
        const chain = {
          select: vi.fn(() => {
            const selectChain: any = {
              order: vi.fn(() => {
                if (table === 'trades') {
                  return Promise.resolve({
                    data: mockTrades,
                    error: null
                  });
                }
                return Promise.resolve({ data: [], error: null });
              }),
              then: function(resolve: any) {
                if (table === 'portfolio') {
                  resolve({
                    data: mockPortfolio,
                    error: null
                  });
                }
              }
            };
            return selectChain;
          })
        };
        return chain;
      }),
      channel: vi.fn((channelName) => ({
        on: vi.fn((_event, _filter, callback) => {
          if (channelName === 'portfolio-changes') portfolioCallback = callback;
          return {
            subscribe: vi.fn()
          };
        }),
      })),
      removeChannel: vi.fn()
    }
  };
});

describe('Dashboard Realtime Behavior', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockTrades = [
      { id: '1', asset_symbol: 'AAPL', price_usd: 150, executed_at: '2026-06-10T10:00:00Z', trade_type: 'BUY', quantity: 1, total_value_usd: 150, ai_justification: '' }
    ];
    mockPortfolio = [
      { asset_symbol: 'USD', balance: 100000 },
      { asset_symbol: 'AAPL', balance: 1 }
    ];
  });

  it('unmounts the entire UI and shows loading when a realtime update arrives', async () => {
    render(<App />);
    
    // Initial load finishes
    await waitFor(() => {
      expect(screen.queryByText('Loading dashboard...')).toBeNull();
    });

    // We should see the dashboard
    expect(screen.getByText('AI Paper Trading Dashboard')).toBeTruthy();

    // Simulate a realtime update from Supabase
    act(() => {
      if (portfolioCallback) {
        portfolioCallback({ new: { asset_symbol: 'AAPL', balance: 2 } });
      }
    });

    // The UI should NOT show Loading dashboard... and should NOT unmount the dashboard
    expect(screen.queryByText('Loading dashboard...')).toBeNull();
    expect(screen.getByText('AI Paper Trading Dashboard')).toBeTruthy();

    // Wait for the simulated fetch to finish
    await waitFor(() => {
      expect(screen.queryByText('Loading dashboard...')).toBeNull();
    });
    
    // UI is still there
    expect(screen.getByText('AI Paper Trading Dashboard')).toBeTruthy();
  });
});
