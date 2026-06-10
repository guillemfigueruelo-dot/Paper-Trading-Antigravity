# Scope: Python Trading Bot

## Architecture
- Bot resides in `/bot` directory.
- Main entry point `main.py` or `bot.py` with CLI argument `--dry-run`.
- Integrates with Supabase (using `supabase-py`).
- Integrates with Finnhub API for market data.
- Integrates with Gemini API via `google-genai` for structured outputs (or `google-generativeai`).
- Needs requirements.txt and .env.example.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Python Bot Implementation | Complete bot logic | M1 (Database) | PLANNED |

## Interface Contracts
- See global PROJECT.md.
