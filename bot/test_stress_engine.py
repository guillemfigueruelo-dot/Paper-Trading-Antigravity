from unittest.mock import patch, MagicMock
from bot.trading.engine import process_decisions

class MockDecision:
    def __init__(self, action, justification):
        self.action = action
        self.justification = justification

@patch('bot.trading.engine.get_supabase_client')
@patch('bot.trading.engine.fetch_portfolio')
@patch('bot.trading.engine.upsert_portfolio_balance')
@patch('bot.trading.engine.insert_trade')
@patch('bot.trading.engine.update_portfolio_balance_optimistic')
def test_over_allocation(mock_opt, mock_insert, mock_upsert, mock_fetch, mock_client):
    db_state = {"USD": 100000.0}
    
    def fake_fetch(client):
        return dict(db_state)
    mock_fetch.side_effect = fake_fetch
    mock_client.return_value = MagicMock()
    
    def fake_opt(client, symbol, old_val, new_val):
        if float(db_state.get(symbol, 0.0)) == float(old_val):
            db_state[symbol] = float(new_val)
            return True
        return False
    mock_opt.side_effect = fake_opt
    
    quotes = {f"SYM{i}": {"current_price": 100.0} for i in range(15)}
    decisions = {f"SYM{i}": MockDecision("BUY", "test") for i in range(15)}
    
    process_decisions(quotes, decisions, dry_run=False)
    
    executed_trades = []
    for call in mock_insert.call_args_list:
        trade_data = call[0][1]
        executed_trades.append(trade_data)
        
    total_spent = sum(t['total_value_usd'] for t in executed_trades)
    assert total_spent <= 100000.0
