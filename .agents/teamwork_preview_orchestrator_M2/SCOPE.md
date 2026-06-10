# Scope: Milestone 2 - Python Trading Bot

## Architecture
- **Backend (Python Bot)**: Python script fetching data from Finnhub, using Google AI Studio (Gemini) for trading decisions, and updating Supabase. Support for dry-run.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | M2 | Python Trading Bot implementation and fixes | none | IN_PROGRESS |

## Interface Contracts
### Bot ↔ Database
- Bot queries `portfolio` for USD balances and asset holdings.
- Bot inserts trade records into `trades` table.
- Bot updates `portfolio` balance and asset holdings after trade.
### Bot ↔ External APIs
- Finnhub API for market data (XAU/USD, AAPL, TSLA, MSFT, GOOGL, AMZN).
- Google AI Studio API for trade decisions (BUY, SELL, HOLD + justification).
