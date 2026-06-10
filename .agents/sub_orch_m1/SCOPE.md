# Scope: M1 - Database Initialization

## Architecture
- **Database (Supabase)**: `portfolio` (USD balances, asset quantities), `trades` (trade history).
- PostgreSQL schema in `/db` directory.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Database Initialization | SQL schema for `portfolio` and `trades` | none | DONE |

## Interface Contracts
### Bot ↔ Database
- Bot queries `portfolio` for USD balances and asset holdings.
- Bot inserts trade records into `trades` table.
- Bot updates `portfolio` balance and asset holdings after trade.
### Dashboard ↔ Database
- Dashboard reads `portfolio` and `trades` to display current state and history.
