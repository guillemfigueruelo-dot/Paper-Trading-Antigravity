import { render, screen, waitFor, act } from '@testing-library/react';
import App from './App';
import { vi, describe, it, expect, beforeEach } from 'vitest';

let triggerPortfolioChange: any;

vi.mock('./lib/supabase', () => {
  return {
    supabase: {
      from: vi.fn((table) => {
        const chain: any = {
          select: vi.fn(() => chain),
          eq: vi.fn(() => chain),
          order: vi.fn(() => chain),
          limit: vi.fn(() => chain),
          maybeSingle: vi.fn(() => Promise.resolve({ data: null, error: null })),
          then: function(resolve: any) {
            if (table === 'portfolio') {
              resolve({ data: [{ asset_symbol: 'USD', balance: 100000 }], error: null });
            } else {
              resolve({ data: [], error: null });
            }
          }
        };
        return chain;
      }),
      channel: vi.fn(() => ({
        on: vi.fn((_event, filter, callback) => {
          if (filter.table === 'portfolio') {
            triggerPortfolioChange = callback;
          }
          return { subscribe: vi.fn() };
        }),
        subscribe: vi.fn()
      })),
      removeChannel: vi.fn()
    }
  };
});

describe('Dashboard Reactivity Stress Test', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('does not unmount dashboard when real-time update arrives', async () => {
    render(<App />);
    
    // Wait for initial load
    await waitFor(() => {
      expect(screen.queryByText('Loading dashboard...')).toBeNull();
    });

    expect(screen.getByText('AI Paper Trading Dashboard')).toBeTruthy();

    // Trigger real-time update
    act(() => {
      triggerPortfolioChange();
    });

    // The screen should NOT show "Loading dashboard..." and unmount the header
    // But currently, App.tsx sets loading to true unconditionally in fetchData
    expect(screen.queryByText('Loading dashboard...')).toBeNull();
    expect(screen.queryByText('AI Paper Trading Dashboard')).toBeTruthy();
  });
});
