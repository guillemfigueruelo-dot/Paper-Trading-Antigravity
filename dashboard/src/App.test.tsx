import { render, screen, waitFor } from '@testing-library/react';
import App from './App';
import { vi, describe, it, expect } from 'vitest';

const mockTradesData = [{
  id: '1',
  asset_symbol: 'BTC',
  trade_type: 'BUY',
  quantity: 1.5,
  price_usd: 50000,
  total_value_usd: 75000,
  ai_justification: 'Strong technical indicators',
  executed_at: '2026-06-10T10:00:00Z'
}];

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
              const latest = mockTradesData.find(t => t.asset_symbol === chain._currentAsset);
              return Promise.resolve({ data: latest || null, error: null });
            }
            return Promise.resolve({ data: null, error: null });
          }),
          then: function(resolve: any) {
            if (table === 'portfolio') {
              resolve({
                data: [
                  { asset_symbol: 'USD', balance: 120000 },
                  { asset_symbol: 'BTC', balance: 1.5 }
                ],
                error: null
              });
            } else if (table === 'trades') {
              resolve({ data: mockTradesData, error: null });
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

describe('App component', () => {
  it('renders expected fields and performance calculation', async () => {
    render(<App />);
    
    // Wait for the mock data to load
    await waitFor(() => {
      expect(screen.queryByText('Loading dashboard...')).toBeNull();
    });

    // Check USD balance contains 120 (since formatting varies by locale)
    expect(screen.getByText((content) => content.includes('120') && content.includes('$'))).toBeTruthy();

    // Check Performance calculation
    // Initial is 100k, Portfolio is 195k (120k USD + 1.5 BTC @ 50k) -> +95%
    expect(screen.getByText((content) => content.includes('95.00%'))).toBeTruthy();

    // Check AI Justification
    expect(screen.getByText('Strong technical indicators')).toBeTruthy();

    // Check Portfolio
    expect(screen.getAllByText('BTC').length).toBeGreaterThan(0);
    expect(screen.getByText('1.50000000')).toBeTruthy();
  });
});
