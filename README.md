<!-- mcp-name: io.github.sepehr071/tsetmc-mcp -->

<div align="center">

<img src="https://raw.githubusercontent.com/sepehr071/tsetmc-mcp/main/.github/banner.png" alt="tsetmc-mcp: unofficial TSETMC MCP server for Claude, Cursor and Copilot" width="100%">

</div>

# tsetmc-mcp: Tehran Stock Exchange MCP server for AI agents

An unofficial, read-only MCP server for [TSETMC](https://tsetmc.com) (مدیریت فناوری بورس تهران), the Tehran Stock Exchange
and Iran Fara Bourse data portal: quotes, top movers, order book, daily history, real vs legal trading and indices.

## For AI agents

- **What:** unofficial MCP server for tsetmc.com market data. Persian queries work for symbol search (Arabic ي/ك are accepted).
- **Install:** `uvx tsetmc-mcp` or `claude mcp add tsetmc -- uvx tsetmc-mcp`. Transport: stdio. Needs [uv](https://docs.astral.sh/uv/getting-started/installation/) (Python 3.10+).
- **Auth:** none. Optional `TSETMC_MCP_PROXY` (HTTP proxy URL, or a comma-separated list); system proxy settings are ignored.
- **Access:** read-only, so no confirmation is needed before calling any tool.
- **Tools:** 8, all prefixed `ts_`. Typical sequence: `ts_indices` -> `ts_market_movers` -> `ts_get_quote` -> `ts_price_history`.
- **Output:** compact JSON. Prices are in **Rial** (Toman = Rial / 10), volumes in shares, dates Gregorian.
- **Network:** tsetmc.com only answers some networks. If you get HTTP 403, try an Iranian connection or set `TSETMC_MCP_PROXY`.
- **Machine-readable:** [`server.json`](server.json).

## Tools

| Tool | Purpose |
|---|---|
| `ts_search_symbols` | Find Tehran Stock Exchange instruments (shares, funds, rights, bonds) by ticker or name |
| `ts_get_quote` | Latest price, daily range, volume and key facts of one instrument on the Tehran Stock Exchange |
| `ts_market_movers` | Top traded instruments of a market today, ranked by gain, loss, volume, value or trade count |
| `ts_order_book` | Best five bid and ask levels (price, volume, order count) of one instrument |
| `ts_price_history` | Daily open, high, low, close, volume, trades and value of one instrument for its latest trading days, newest first |
| `ts_real_legal` | Buy and sell volume, value and buyer/seller counts split by real (individual) and legal (institutional) traders per day |
| `ts_indices` | TSE total index, market state and trading totals, plus every sector and market index with its change |
| `ts_index_history` | Daily close, high, low and percent change of a TSE index (total, equal-weight, sector...), newest first |

## Reply size

Every reply stays under about 15 KB: `ts_market_movers` returns at most 30 rows, `ts_price_history` 50 days, `ts_index_history` 100 days, `ts_real_legal` 10 days.
The order book is empty outside trading hours (Saturday to Wednesday mornings); other tools then show the last session.

## Development

```bash
uv sync
uv run ruff check . && uv run ruff format --check .
uv run python -m pytest -q          # offline unit tests
uv run python -m pytest -m live -q  # calls tsetmc.com
uv build
```

Not affiliated with TSETMC. Data is informational and may be delayed; not financial advice. MIT license.
