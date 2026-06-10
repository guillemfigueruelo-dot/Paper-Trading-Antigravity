from supabase import create_client, Client
from bot.config import SUPABASE_URL, SUPABASE_KEY

def get_supabase_client() -> Client:
    # If no URL or Key, return None (useful for dry-run if we don't have real creds yet)
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_portfolio(client: Client) -> dict:
    if not client:
        return {}
    response = client.table("portfolio").select("*").execute()
    # return a dict mapping asset_symbol to balance
    return {row["asset_symbol"]: row["balance"] for row in response.data}

def upsert_portfolio_balance(client: Client, asset_symbol: str, balance: float):
    if not client:
        return
    client.table("portfolio").upsert({"asset_symbol": asset_symbol, "balance": balance}).execute()

def insert_trade(client: Client, trade_data: dict):
    if not client:
        return
    client.table("trades").insert(trade_data).execute()
