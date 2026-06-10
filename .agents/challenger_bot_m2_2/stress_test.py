import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from bot.trading.engine import process_decisions

class MockDecision:
    def __init__(self, action, justification):
        self.action = action
        self.justification = justification

def test_trade_sizing_equality():
    print("--- Running Test: Trade Sizing Equality ---")
    num_assets = 10
    
    quotes = {}
    decisions = {}
    
    for i in range(num_assets):
        symbol = f"ASSET_{i}"
        quotes[symbol] = {"current_price": 100.0}
        decisions[symbol] = MockDecision("BUY", f"Test {i}")
        
    with patch('bot.trading.engine.get_supabase_client') as mock_client, \
         patch('bot.trading.engine.fetch_portfolio') as mock_fetch, \
         patch('bot.trading.engine.upsert_portfolio_balance') as mock_upsert, \
         patch('bot.trading.engine.insert_trade') as mock_insert:
         
        mock_fetch.return_value = {"USD": 100000.0}
        mock_client.return_value = MagicMock()
        
        process_decisions(quotes, decisions, dry_run=False)
        
        executed_trades = []
        for call in mock_insert.call_args_list:
            trade_data = call[0][1]
            executed_trades.append(trade_data)
            
        print("\nTrades executed:")
        for t in executed_trades:
            print(f"{t['asset_symbol']}: Allocated USD {t['total_value_usd']:.2f}")
            
        first_size = executed_trades[0]['total_value_usd']
        last_size = executed_trades[-1]['total_value_usd']
        
        if first_size != last_size:
            print(f"FAIL: Trade sizes shrink! First asset got ${first_size:.2f}, Last asset got ${last_size:.2f}")
            sys.exit(1)
        else:
            print("PASS: Trade sizes are equal.")

if __name__ == "__main__":
    test_trade_sizing_equality()
