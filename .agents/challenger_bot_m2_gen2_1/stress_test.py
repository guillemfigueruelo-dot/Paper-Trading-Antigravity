import sys
import os

# Add workspace directory to sys path so we can import bot module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from bot.trading.engine import process_decisions

class MockDecision:
    def __init__(self, action, justification="test"):
        self.action = action
        self.justification = justification

def test_12_buys():
    quotes = {f"SYM_{i}": {"current_price": 100.0} for i in range(12)}
    decisions = {f"SYM_{i}": MockDecision("BUY") for i in range(12)}
    
    import unittest.mock as mock
    with mock.patch('bot.trading.engine.get_supabase_client') as mock_client, \
         mock.patch('bot.trading.engine.fetch_portfolio') as mock_fetch, \
         mock.patch('bot.trading.engine.upsert_portfolio_balance') as mock_upsert, \
         mock.patch('bot.trading.engine.insert_trade') as mock_insert:
        
        mock_fetch.return_value = {"USD": 100000.0}
        
        # Capture stdout
        from io import StringIO
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        
        process_decisions(quotes, decisions, dry_run=False)
        
        output = sys.stdout.getvalue()
        sys.stdout = old_stdout
        
        executed_trades = []
        for call in mock_insert.call_args_list:
            trade_data = call[0][1]
            executed_trades.append(trade_data)
        
        return executed_trades, output

if __name__ == "__main__":
    trades, output = test_12_buys()
    for t in trades:
        print(f"Trade: {t['asset_symbol']}, Size: {t['total_value_usd']}")
    print(f"Total trades executed: {len(trades)}")
    print("--- process_decisions Output ---")
    print(output)
