from bot.clients.supabase_client import get_supabase_client, fetch_portfolio, upsert_portfolio_balance, insert_trade, update_portfolio_balance_optimistic

def process_decisions(quotes: dict, decisions: dict, dry_run: bool = False):
    """
    Process trade decisions sequentially.
    """
    client = get_supabase_client()
    
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
        portfolio["USD"] = 100000.00

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

        if current_price <= 0:
            continue

        asset_balance = float(portfolio.get(symbol, 0.0))

        if asset_balance > 0:
            quantity = round(asset_balance, 6)
            if quantity <= 0:
                print(f"Zero quantity calculated for {symbol}. Skipping.")
                continue

            total_value = quantity * current_price
            
            if not dry_run:
                success = False
                for _ in range(3):
                    current_portfolio = fetch_portfolio(client)
                    current_usd = float(current_portfolio.get("USD", 0.0))
                    current_asset = float(current_portfolio.get(symbol, 0.0))
                    
                    if current_asset <= 0:
                        break
                        
                    qty_to_sell = round(current_asset, 6)
                    if qty_to_sell <= 0:
                        break
                        
                    value = qty_to_sell * current_price
                    new_usd = current_usd + value
                    
                    if update_portfolio_balance_optimistic(client, "USD", current_usd, new_usd):
                        upsert_portfolio_balance(client, symbol, 0.0)
                        success = True
                        portfolio["USD"] = new_usd
                        portfolio[symbol] = 0.0
                        quantity = qty_to_sell
                        total_value = value
                        break
                
                if success:
                    insert_trade(client, {
                        "asset_symbol": symbol,
                        "trade_type": "SELL",
                        "quantity": quantity,
                        "price_usd": current_price,
                        "total_value_usd": total_value,
                        "ai_justification": justification
                    })
            else:
                portfolio["USD"] += total_value
                portfolio[symbol] = 0.0

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

        if current_price <= 0:
            continue

        usd_balance = float(portfolio.get("USD", 0.0))
        
        if usd_balance >= 0.01:
            allocated_usd = min(base_allocation, usd_balance)
            quantity = round(allocated_usd / current_price, 6)
            
            if quantity <= 0:
                print(f"Zero quantity calculated for {symbol}. Skipping.")
                continue
                
            actual_cost = quantity * current_price
            
            if not dry_run:
                success = False
                for _ in range(3):
                    current_portfolio = fetch_portfolio(client)
                    current_usd = float(current_portfolio.get("USD", 0.0))
                    current_asset = float(current_portfolio.get(symbol, 0.0))
                    
                    if current_usd < 0.01:
                        break
                        
                    alloc_usd = min(base_allocation, current_usd)
                    qty_to_buy = round(alloc_usd / current_price, 6)
                    
                    if qty_to_buy <= 0:
                        break
                        
                    cost = qty_to_buy * current_price
                    new_usd = current_usd - cost
                    new_asset = current_asset + qty_to_buy
                    
                    if update_portfolio_balance_optimistic(client, "USD", current_usd, new_usd):
                        upsert_portfolio_balance(client, symbol, new_asset)
                        success = True
                        portfolio["USD"] = new_usd
                        portfolio[symbol] = new_asset
                        quantity = qty_to_buy
                        actual_cost = cost
                        break
                
                if success:
                    insert_trade(client, {
                        "asset_symbol": symbol,
                        "trade_type": "BUY",
                        "quantity": quantity,
                        "price_usd": current_price,
                        "total_value_usd": actual_cost,
                        "ai_justification": justification
                    })
            else:
                portfolio["USD"] -= actual_cost
                portfolio[symbol] = float(portfolio.get(symbol, 0.0)) + quantity
        else:
            print(f"Insufficient USD balance to BUY {symbol}.")

    # Pass 3: HOLDs and Unknowns
    for symbol, decision in decisions.items():
        if decision.action not in ["BUY", "SELL"]:
            print(f"ACTION: {decision.action} {symbol}.")

    print(f"\n--- Final USD Balance: ${portfolio['USD']:.2f} ---")
