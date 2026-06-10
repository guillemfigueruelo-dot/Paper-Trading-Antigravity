import { useEffect, useState } from 'react';
import { supabase } from './lib/supabase';
import './App.css';

interface PortfolioAsset {
  asset_symbol: string;
  balance: number;
}

interface Trade {
  id: string;
  asset_symbol: string;
  trade_type: 'BUY' | 'SELL';
  quantity: number;
  price_usd: number;
  total_value_usd: number;
  ai_justification: string;
  executed_at: string;
}

function App() {
  const [portfolio, setPortfolio] = useState<PortfolioAsset[]>([]);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [usdBalance, setUsdBalance] = useState<number>(0);
  const [loading, setLoading] = useState(true);
  const [latestPrices, setLatestPrices] = useState<Record<string, number>>({});

  useEffect(() => {
    async function fetchData(isInitial: boolean = false) {
      if (isInitial) setLoading(true);
      try {
        const { data: portfolioData, error: portfolioError } = await supabase
          .from('portfolio')
          .select('*');

        if (portfolioError) throw portfolioError;

        let currentPortfolio: PortfolioAsset[] = [];
        if (portfolioData) {
          const usd = portfolioData.find((p) => p.asset_symbol === 'USD');
          setUsdBalance(usd ? Number(usd.balance) : 0);
          currentPortfolio = portfolioData
            .filter((p) => p.asset_symbol !== 'USD')
            .map((p) => ({ ...p, balance: Number(p.balance) }));
          setPortfolio(currentPortfolio);
        }

        const prices: Record<string, number> = {};
        await Promise.all(
          currentPortfolio.map(async (asset) => {
            const { data } = await supabase
              .from('trades')
              .select('price_usd')
              .eq('asset_symbol', asset.asset_symbol)
              .order('executed_at', { ascending: false })
              .limit(1)
              .maybeSingle();
            
            if (data) {
              prices[asset.asset_symbol] = Number(data.price_usd);
            }
          })
        );
        setLatestPrices(prices);

        const { data: tradesData, error: tradesError } = await supabase
          .from('trades')
          .select('*')
          .order('executed_at', { ascending: false })
          .limit(100);

        if (tradesError) throw tradesError;
        if (tradesData) {
          setTrades(
            tradesData.map((t) => ({
              ...t,
              quantity: Number(t.quantity),
              price_usd: Number(t.price_usd),
              total_value_usd: Number(t.total_value_usd),
            }))
          );
        }
      } catch (error) {
        console.error('Error fetching data:', error);
      } finally {
        if (isInitial) setLoading(false);
      }
    }

    fetchData(true);

    // Subscribe to changes
    const portfolioSub = supabase
      .channel('portfolio-changes')
      .on(
        'postgres_changes',
        { event: '*', schema: 'public', table: 'portfolio' },
        () => fetchData(false)
      )
      .subscribe();

    const tradesSub = supabase
      .channel('trades-changes')
      .on(
        'postgres_changes',
        { event: '*', schema: 'public', table: 'trades' },
        () => fetchData(false)
      )
      .subscribe();

    return () => {
      supabase.removeChannel(portfolioSub);
      supabase.removeChannel(tradesSub);
    };
  }, []);

  if (loading) {
    return <div className="container">Loading dashboard...</div>;
  }

  const INITIAL_CAPITAL = 100000;

  // Calculate total portfolio value using the separately fetched latest prices
  let totalPortfolioValue = usdBalance;
  portfolio.forEach((asset) => {
    const price = latestPrices[asset.asset_symbol];
    if (price !== undefined) {
      totalPortfolioValue += asset.balance * price;
    }
  });

  return (
    <div className="container">
      <header>
        <h1>AI Paper Trading Dashboard</h1>
      </header>

      <main>
        <div className="summary-cards">
          <div className="card">
            <h2>Total Value</h2>
            <p className="big-number">${totalPortfolioValue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
          </div>
          <div className="card">
            <h2>USD Balance</h2>
            <p className="big-number">${usdBalance.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
          </div>
          <div className="card">
            <h2>Asset Count</h2>
            <p className="big-number">{portfolio.length}</p>
          </div>
          <div className="card">
            <h2>Performance vs Initial ($100k)</h2>
            <p className="big-number" style={{ color: totalPortfolioValue >= INITIAL_CAPITAL ? 'green' : 'red' }}>
              {(((totalPortfolioValue - INITIAL_CAPITAL) / INITIAL_CAPITAL) * 100).toFixed(2)}%
            </p>
          </div>
        </div>

        <section className="portfolio-section">
          <h2>Asset Portfolio</h2>
          {portfolio.length === 0 ? (
            <p>No assets currently held.</p>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Balance</th>
                </tr>
              </thead>
              <tbody>
                {portfolio.map((asset) => (
                  <tr key={asset.asset_symbol}>
                    <td>{asset.asset_symbol}</td>
                    <td>{asset.balance.toFixed(8)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>

        <section className="trades-section">
          <h2>Trade History</h2>
          {trades.length === 0 ? (
            <p>No trades executed yet.</p>
          ) : (
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Type</th>
                    <th>Symbol</th>
                    <th>Quantity</th>
                    <th>Price (USD)</th>
                    <th>Total (USD)</th>
                    <th>AI Justification</th>
                  </tr>
                </thead>
                <tbody>
                  {trades.map((trade) => (
                    <tr key={trade.id}>
                      <td>{new Date(trade.executed_at).toLocaleString()}</td>
                      <td className={trade.trade_type === 'BUY' ? 'buy' : 'sell'}>{trade.trade_type}</td>
                      <td>{trade.asset_symbol}</td>
                      <td>{trade.quantity}</td>
                      <td>${trade.price_usd.toFixed(2)}</td>
                      <td>${trade.total_value_usd.toFixed(2)}</td>
                      <td className="justification">{trade.ai_justification || 'N/A'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;
