from bot.clients.supabase_client import get_supabase_client, fetch_portfolio, upsert_portfolio_balance, insert_trade

def process_decisions(quotes: dict, decisions: dict, dry_run: bool = False):
    """
    Process trade decisions sequentially.
    quotes: {symbol: {"symbol": ..., "current_price": ...}}
    decisions: {symbol: TradeDecision}
    """
    client = get_supabase_client()
    
    # In dry-run, we might not have a client or we might just want to print.
    # We will fetch the actual portfolio if possible, otherwise mock it.
    try:
        portfolio = fetch_portfolio(client) if client else {}
    except Exception as e:
        print(f"Failed to fetch portfolio: {e}")
        if not dry_run:
            raise RuntimeError(f"Aborting execution: Failed to fetch portfolio: {e}")
        portfolio = {}

    if not portfolio and not dry_run and client:
        print("Seeding Supabase with initial $100,000.00 USD balance.")
        upsert_portfolio_balance(client, "USD", 100000.00)
        portfolio["USD"] = 100000.00

    if "USD" not in portfolio:
        portfolio["USD"] = 100000.00  # Default fallback if DB is empty or dry-run without creds

    # Pass 1: SELLs
    for symbol, decision in decisions.items():
        if decision.action != "SELL":
            continue
            
        quote = quotes.get(symbol, {})
        current_price = float(quote.get("current_price", 0.0))
        justification = decision.justification
        
        print(f"\nProcessing {symbol}:")
        print(f"Price: ${current_price:.2f}")
        print(f"Decision: SELL")
        print(f"Justification: {justification}")

        if current_price <= 0:
            print(f"Invalid price {current_price} for {symbol}. Skipping.")
            continue

        asset_balance = float(portfolio.get(symbol, 0.0))
        usd_balance = float(portfolio["USD"])

        if asset_balance > 0:
            quantity = round(asset_balance, 6)
            total_value = quantity * current_price
            
            print(f"ACTION: SELL {quantity:.6f} {symbol} for ${total_value:.2f}")
            
            # Update local state unconditionally
            portfolio["USD"] = usd_balance + total_value
            portfolio[symbol] = 0.0
            
            if not dry_run:
                # Update DB
                upsert_portfolio_balance(client, "USD", portfolio["USD"])
                upsert_portfolio_balance(client, symbol, 0.0)
                
                trade_data = {
                    "asset_symbol": symbol,
                    "trade_type": "SELL",
                    "quantity": quantity,
                    "price_usd": current_price,
                    "total_value_usd": total_value,
                    "ai_justification": justification
                }
                insert_trade(client, trade_data)
                print(f"Executed SELL in DB.")
        else:
            print(f"No asset balance to SELL {symbol}.")

    # Recalculate Dynamic Allocation for BUYs based on the new USD balance
    usd_balance_after_sells = float(portfolio.get("USD", 0.0))
    base_allocation = usd_balance_after_sells * 0.10

    # Pass 2: BUYs
    for symbol, decision in decisions.items():
        if decision.action != "BUY":
            continue
            
        quote = quotes.get(symbol, {})
        current_price = float(quote.get("current_price", 0.0))
        justification = decision.justification
        
        print(f"\nProcessing {symbol}:")
        print(f"Price: ${current_price:.2f}")
        print(f"Decision: BUY")
        print(f"Justification: {justification}")

        if current_price <= 0:
            print(f"Invalid price {current_price} for {symbol}. Skipping.")
            continue

        asset_balance = float(portfolio.get(symbol, 0.0))
        usd_balance = float(portfolio["USD"])

        if usd_balance > 0:
            allocated_usd = min(base_allocation, usd_balance)
            quantity = round(allocated_usd / current_price, 6)
            
            print(f"ACTION: BUY {quantity:.6f} {symbol} for ${allocated_usd:.2f}")
            
            # Update local state unconditionally
            portfolio["USD"] = usd_balance - allocated_usd
            portfolio[symbol] = asset_balance + quantity
            
            if not dry_run:
                # Update DB
                upsert_portfolio_balance(client, "USD", portfolio["USD"])
                upsert_portfolio_balance(client, symbol, portfolio[symbol])
                
                trade_data = {
                    "asset_symbol": symbol,
                    "trade_type": "BUY",
                    "quantity": quantity,
                    "price_usd": current_price,
                    "total_value_usd": allocated_usd,
                    "ai_justification": justification
                }
                insert_trade(client, trade_data)
                print(f"Executed BUY in DB.")
        else:
            print(f"Insufficient USD balance to BUY {symbol}.")

    # Pass 3: HOLDs and Unknowns
    for symbol, decision in decisions.items():
        action = decision.action
        if action == "HOLD":
            print(f"ACTION: HOLD {symbol}. No trade executed.")
        elif action not in ["BUY", "SELL", "HOLD"]:
            print(f"Unknown action {action} for {symbol}.")

    print(f"\n--- Final USD Balance: ${portfolio['USD']:.2f} ---")
