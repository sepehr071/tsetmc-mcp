<!-- mcp-name: io.github.sepehr071/tsetmc-mcp -->

<div align="center">

<img src="https://raw.githubusercontent.com/sepehr071/tsetmc-mcp/main/.github/banner.png" alt="tsetmc-mcp: unofficial TSETMC MCP server for Claude, Cursor and Copilot" width="100%">

# tsetmc-mcp: Tehran Stock Exchange MCP server for AI agents

**Let your AI agent read the Tehran Stock Exchange (بورس تهران).**<br>
An unofficial, read-only MCP server for TSETMC, the data portal of the Tehran Stock Exchange and Iran Fara Bourse:<br>
quotes, top movers, order book, daily history, real vs legal trading and market indices, from Claude, Cursor or Copilot.

[![PyPI](https://img.shields.io/pypi/v/tsetmc-mcp?color=2563eb)](https://pypi.org/project/tsetmc-mcp/)
[![Python](https://img.shields.io/pypi/pyversions/tsetmc-mcp)](https://pypi.org/project/tsetmc-mcp/)
[![CI](https://github.com/sepehr071/tsetmc-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/sepehr071/tsetmc-mcp/actions/workflows/ci.yml)
[![MCP Registry](https://img.shields.io/badge/MCP_Registry-io.github.sepehr071%2Ftsetmc--mcp-7c3aed)](https://registry.modelcontextprotocol.io/?q=tsetmc-mcp)
[![License: MIT](https://img.shields.io/badge/license-MIT-16a34a)](https://github.com/sepehr071/tsetmc-mcp/blob/main/LICENSE)

[![Install in VS Code](https://img.shields.io/badge/VS_Code-Install_tsetmc--mcp-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect/mcp/install?name=tsetmc&config=%7B%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22tsetmc-mcp%22%5D%7D)

[For AI agents](#for-ai-agents) · [Quick start](#quick-start) · [What it can do](#what-it-can-do) · [Tools](#tools) · [FAQ](#faq) · [فارسی](#فارسی)

</div>

---

## For AI agents

- **What:** unofficial MCP server (model context protocol) for tsetmc.com, the Tehran Stock Exchange and Iran Fara Bourse market data. Symbol search takes Persian names (Arabic ي/ك are accepted).
- **Install:** `uvx tsetmc-mcp` or `claude mcp add tsetmc -- uvx tsetmc-mcp`. Transport: stdio. Needs [uv](https://docs.astral.sh/uv/getting-started/installation/) (Python 3.10+).
- **Auth:** none, no API key or account. Optional `TSETMC_MCP_PROXY` (HTTP proxy URL, or a comma-separated list); system proxy settings are ignored.
- **Access:** read-only. It cannot log in, trade or place orders, so no confirmation is needed before calling any tool.
- **Tools:** 8, all prefixed `ts_`. Typical sequence: `ts_indices` -> `ts_market_movers` -> `ts_get_quote` -> `ts_price_history`.
  If you only have a name, call `ts_search_symbols` first and pass its `symbol` or `ins_code` to the other tools.
- **Use when:** the user asks about Tehran Stock Exchange or Fara Bourse prices, movers, sector indices, order book or real vs legal money flow.
- **Do not use when:** the user wants to trade, needs fundamentals or Codal filings, or asks about other exchanges.
- **Output:** compact JSON. Prices in **Rial** (Toman = Rial / 10), volumes in shares, dates Gregorian (`YYYY-MM-DD`).
- **Network:** tsetmc.com answers only some networks. On HTTP 403, try an Iranian connection or set `TSETMC_MCP_PROXY`.
- **Machine-readable:** [`server.json`](https://github.com/sepehr071/tsetmc-mcp/blob/main/server.json) and the
  [iran-mcp catalog](https://github.com/sepehr071/iran-mcp).

## Why

TSETMC is the place Iranian traders look at, but it is a heavy web page built for human eyes. Asking "which sectors
are up today, which stocks hit the daily limit, and are individual investors buying or selling Foolad?" means opening
several screens. With `tsetmc-mcp` an agent answers it in a few calls and returns a short summary instead of tables
of raw numbers.

> **You:** How is the market today, and what are the biggest gainers?
>
> **Agent:** *calls* `ts_indices(limit=5)` -> `ts_market_movers(market="bourse", sort_by="gain", limit=5)`
>
> It reads the total index, the market state and the strongest sector indices, then lists the top gainers with
> their last price, change and whether they are stuck at the upper price limit.

Every reply is trimmed to stay under about 15 KB, so it does not flood the agent's context.

## What it can do

- **Look up** any share, fund, rights issue or bond on the Tehran Stock Exchange or Iran Fara Bourse by ticker or name
- **Quote** one instrument: last trade, closing price, daily range, volume, trades, value, allowed price range, week and year range, shares outstanding and market cap
- **Rank movers** of Bourse, Fara Bourse, rights or bonds by gain, loss, volume, value or trade count, with a flag for prices at the daily limit
- **Read the order book**: best five bid and ask levels with price, volume and order count, including buy and sell queues
- **Pull daily history**: open, high, low, close, volume, trades and value for up to 50 trading days
- **Track real vs legal trading** (حقیقی و حقوقی): buy and sell volume, value and counts per day, plus net individual volume
- **Scan indices**: the total index, equal-weight index, market state and every sector index, and up to 100 days of any index's history
- **Read-only by design**: no login, no orders

Example prompts:

- "Which TSE sectors are leading today?"
- "Top 10 Fara Bourse stocks by traded value."
- "Show the order book for فولاد."
- "Last 20 trading days of وبملت, and did individual investors buy or sell over the last 3 days?"
- "How has the total index moved over the last 30 days?"
- <span dir="rtl">شاخص کل امروز چقدر تغییر کرده و کدام صنعت&zwnj;ها بیشترین رشد را داشتند؟</span>
- <span dir="rtl">ورود و خروج پول حقیقی فولاد در سه روز اخیر چطور بوده؟</span>
- <span dir="rtl">بیشترین حجم معاملات امروز فرابورس مربوط به کدام نمادهاست؟</span>

## Quick start

You need [uv](https://docs.astral.sh/uv/getting-started/installation/). No API key or account.

<details open>
<summary><b>Claude Code</b></summary>

```bash
claude mcp add tsetmc -- uvx tsetmc-mcp
```
</details>

<details>
<summary><b>Claude Desktop</b></summary>

Settings → Developer → Edit Config, then add:

```json
{
  "mcpServers": {
    "tsetmc": { "command": "uvx", "args": ["tsetmc-mcp"] }
  }
}
```
</details>

<details>
<summary><b>Cursor</b></summary>

Add the Claude Desktop block above to `~/.cursor/mcp.json` (or `.cursor/mcp.json` in a project).
</details>

<details>
<summary><b>VS Code (Copilot agent mode)</b></summary>

Click **Install in VS Code** above, or add to `.vscode/mcp.json`:

```json
{
  "servers": {
    "tsetmc": { "type": "stdio", "command": "uvx", "args": ["tsetmc-mcp"] }
  }
}
```
</details>

<details>
<summary><b>Codex CLI</b></summary>

```bash
codex mcp add tsetmc -- uvx tsetmc-mcp
```

Or in `~/.codex/config.toml`:

```toml
[mcp_servers.tsetmc]
command = "uvx"
args = ["tsetmc-mcp"]
```
</details>

<details>
<summary><b>Gemini CLI</b></summary>

Add to `~/.gemini/settings.json`:

```json
{
  "mcpServers": {
    "tsetmc": { "command": "uvx", "args": ["tsetmc-mcp"] }
  }
}
```
</details>

<details>
<summary><b>Windsurf</b></summary>

Add the Claude Desktop block to `~/.codeium/windsurf/mcp_config.json`.
</details>

<details>
<summary><b>Anything else</b></summary>

It is a standard stdio MCP server: run `uvx tsetmc-mcp`, or `pip install tsetmc-mcp` and run `tsetmc-mcp`.
</details>

## Tools

Pass a ticker (`فولاد`), an exact name, or a numeric `ins_code` as `symbol`. Index tools take an index name such as `شاخص کل`.

| Tool | What it does |
|---|---|
| `ts_search_symbols` | Find Tehran Stock Exchange instruments (shares, funds, rights, bonds) by ticker or name |
| `ts_get_quote` | Latest price, daily range, volume and key facts of one instrument on the Tehran Stock Exchange |
| `ts_market_movers` | Top traded instruments of a market today, ranked by gain, loss, volume, value or trade count |
| `ts_order_book` | Best five bid and ask levels (price, volume, order count) of one instrument |
| `ts_price_history` | Daily open, high, low, close, volume, trades and value of one instrument for its latest trading days, newest first |
| `ts_real_legal` | Buy and sell volume, value and buyer/seller counts split by real (individual) and legal (institutional) traders per day |
| `ts_indices` | TSE total index, market state and trading totals, plus every sector and market index with its change |
| `ts_index_history` | Daily close, high, low and percent change of a TSE index (total, equal-weight, sector...), newest first |

All 8 tools are annotated `readOnlyHint: true`.

## How it works

```text
  AI agent  (Claude, Cursor, Copilot, ...)
      │
      │  MCP over stdio
      ▼
  tsetmc-mcp  (runs on your machine)
      │
      │  HTTPS
      └──────▶  cdn.tsetmc.com   quotes, market watch, order book, indices
```

`tsetmc-mcp` runs locally and calls the same endpoints the tsetmc.com site uses. It has no hosted server in between
and no API key. The TSETMC API is undocumented and blocks plain HTTP clients, so requests go out through a
Chrome-impersonating client. It sends at most 2 requests at a time with a little jitter, keeps answers for 15 seconds,
retries a failed GET up to twice, and only talks to `cdn.tsetmc.com`. It only reads.

## Good to know

- **Prices are in Rial**, as TSETMC quotes them. Divide by 10 for Toman. Volumes are in shares.
- **Prices are not adjusted** for capital increases or dividends, so long histories can show jumps.
- **`last` vs `close`:** `last` is the last trade, `close` the closing (volume-weighted) price; `change_pct` compares `last` with yesterday's close.
- **Trading hours:** the market trades Saturday to Wednesday, in the morning. Outside those hours the order book is empty and other tools show the last session.
- **Network:** tsetmc.com blocks some networks with HTTP 403. It worked from an Iranian line; a foreign exit may or may not be accepted. If you get 403, set `TSETMC_MCP_PROXY` to an HTTP proxy with an Iranian exit. System proxy variables are ignored on purpose.
- **Reply caps:** `ts_market_movers` returns at most 30 rows, `ts_price_history` 50 days, `ts_index_history` 100 days, `ts_real_legal` 10 days, `ts_indices` 60 indices.
- **`ts_real_legal` makes one upstream call per day**, so ask for few days. Days with no data are listed under `unavailable_dates`.
- **Movers cover four markets:** `bourse`, `farabourse`, `rights` and `bonds`. Only instruments that traded today are ranked.
- **Names:** Arabic ي/ك and Persian ی/ک both match, and answers use the Persian forms. An ambiguous name returns an error listing candidates; pass the exact ticker or `ins_code`.
- **What it does not do:** no trading or orders, no company fundamentals or Codal filings, no options or futures movers, no adjusted prices, no Jalali dates. Rate limits of TSETMC are unknown, so keep requests reasonable.

## FAQ

<details>
<summary><b>Is there a TSETMC API or Tehran Stock Exchange MCP server?</b></summary>

TSETMC has no documented public API. `tsetmc-mcp` is an unofficial MCP server with 8 read-only tools that calls the
same endpoints the tsetmc.com web app uses and returns compact JSON for AI agents.
</details>

<details>
<summary><b>Does it cover Fara Bourse (فرابورس) too?</b></summary>

Yes. `ts_market_movers` accepts `market="farabourse"`, and `ts_search_symbols` finds Fara Bourse instruments;
each match shows its market.
</details>

<details>
<summary><b>How do I use it with Claude, Cursor or Copilot?</b></summary>

Add the server with `claude mcp add tsetmc -- uvx tsetmc-mcp`, or use the matching config in
[Quick start](#quick-start), then ask in plain language, in Persian or English.
</details>

<details>
<summary><b>Are prices in Rial or Toman?</b></summary>

Rial. Every tool reports `unit: "rial"` where it returns prices. Divide by 10 for Toman.
</details>

<details>
<summary><b>Why is the order book empty?</b></summary>

The order book is only open while the market is. TSETMC trades Saturday to Wednesday mornings; after the close, or
for an instrument that did not trade today, `ts_order_book` returns no levels and a note.
</details>

<details>
<summary><b>I get HTTP 403. What now?</b></summary>

tsetmc.com blocks some networks. Try from an Iranian connection, or set `TSETMC_MCP_PROXY` to an HTTP proxy with an
Iranian exit. Plain `curl` is always refused because the site checks the TLS fingerprint; the server handles that itself.
</details>

<details>
<summary><b>Can it place orders or give investment advice?</b></summary>

No. It has no login and no trading calls, it only reads public market data. Nothing it returns is financial advice.
</details>

<details>
<summary><b>Is the data real time?</b></summary>

It is what TSETMC serves, kept for up to 15 seconds in a local cache, and it may be delayed. Check the `date` and
`time` fields in a quote for the moment of the last trade.
</details>

<details>
<summary><b>How do I debug what the agent sees?</b></summary>

```bash
npx @modelcontextprotocol/inspector uvx tsetmc-mcp
```
</details>

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| `TSETMC_MCP_PROXY` | unset | Optional HTTP proxy URL for tsetmc.com requests; system proxy settings are ignored. A comma-separated list is used one at a time: the next proxy takes over when one is blocked or cannot connect |

<a id="فارسی"></a>

## فارسی: سرور MCP بورس تهران (TSETMC)

<div dir="rtl">

**tsetmc-mcp** یک سرور MCP غیررسمی و فقط&zwnj;خواندنی برای سامانه TSETMC (مدیریت فناوری بورس تهران) است. این سرور به دستیار هوش مصنوعی شما (Claude، Cursor، Copilot و ...) اجازه می&zwnj;دهد
قیمت نماد، شاخص کل، دفتر سفارش و آمار معاملات بورس تهران و فرابورس را بخواند.

**چه کارهایی می&zwnj;کند**

- **جستجوی نماد** سهام، صندوق، حق تقدم و اوراق (با نام یا نماد فارسی؛ «ي» و «ك» عربی هم پذیرفته می&zwnj;شود).
- **قیمت لحظه&zwnj;ای نماد**: آخرین معامله، قیمت پایانی، بازه روز، حجم، ارزش، بازه مجاز قیمت و ارزش بازار.
- **پرمعامله&zwnj;ها و بیشترین رشد و افت** در بورس، فرابورس، حق تقدم و اوراق، با نشانه صف خرید یا فروش (قیمت در سقف یا کف مجاز).
- **دفتر سفارش** با ۵ سطح بهترین خرید و فروش.
- **تاریخچه روزانه** قیمت تا ۵۰ روز معاملاتی (قیمت&zwnj;ها تعدیل نشده&zwnj;اند).
- **حقیقی و حقوقی**: حجم و ارزش خرید و فروش و تعداد خریدار و فروشنده به تفکیک حقیقی و حقوقی، تا ۱۰ روز.
- **شاخص&zwnj;ها**: شاخص کل، شاخص هم&zwnj;وزن، وضعیت بازار و شاخص همه صنعت&zwnj;ها، و تاریخچه تا ۱۰۰ روز.

**نکته&zwnj;ها**

- فقط خواندنی است: وارد حساب نمی&zwnj;شود و سفارش ثبت نمی&zwnj;کند. توصیه سرمایه&zwnj;گذاری نیست.
- قیمت&zwnj;ها به ریال است؛ برای تومان تقسیم بر ۱۰ کنید. تاریخ&zwnj;ها میلادی هستند.
- بازار شنبه تا چهارشنبه، صبح&zwnj;ها باز است؛ بعد از بسته شدن بازار دفتر سفارش خالی است.
- اگر سایت خطای ۴۰۳ داد، از اینترنت ایران استفاده کنید یا متغیر `TSETMC_MCP_PROXY` را روی یک پراکسی HTTP با خروجی ایران بگذارید.
- کلید API لازم نیست و روی سیستم خود شما اجرا می&zwnj;شود.

**نصب** (اول [uv](https://docs.astral.sh/uv/getting-started/installation/) را نصب کنید). در Claude Code:

</div>

```bash
claude mcp add tsetmc -- uvx tsetmc-mcp
```

<div dir="rtl">

در Claude Desktop، Cursor و بقیه برنامه&zwnj;ها همان تنظیم بخش [Quick start](#quick-start) را بگذارید.

**نمونه پرسش&zwnj;ها**

- «شاخص کل امروز چقدر تغییر کرده و کدام صنعت&zwnj;ها جلوتر هستند؟»
- «دفتر سفارش فولاد را نشان بده.»
- «پرمعامله&zwnj;ترین نمادهای فرابورس امروز کدام&zwnj;اند؟»
- «ورود و خروج پول حقیقی وبملت در ۵ روز اخیر چطور بوده؟»
- «تاریخچه ۳۰ روزه شاخص کل را بده.»

</div>

## Development

```bash
git clone https://github.com/sepehr071/tsetmc-mcp && cd tsetmc-mcp
uv sync
uv run ruff check . && uv run ruff format --check .
uv run python -m pytest -q          # offline unit tests
uv run python -m pytest -m live -q  # calls tsetmc.com
uv build
```

All tools live in `src/tsetmc_mcp/markets.py`; each is a typed async function with a docstring that tells the agent
when to use it. Issues and PRs are welcome.

Releases: bump the version in `pyproject.toml` and `server.json`, then push a `v*` tag. GitHub Actions publishes to PyPI.

## Related servers

- [iran-mcp](https://github.com/sepehr071/iran-mcp): catalog of all Iranian-service MCP servers
- [tgju-mcp](https://github.com/sepehr071/tgju-mcp) for dollar, gold, coin and commodity prices from TGJU
- [iran-crypto-mcp](https://github.com/sepehr071/iran-crypto-mcp) for crypto prices on Iranian exchanges
- [milligold-mcp](https://github.com/sepehr071/milligold-mcp) for gold prices on Milli
- [iran-news-mcp](https://github.com/sepehr071/iran-news-mcp) for Iranian news

## Disclaimer

Unofficial and not affiliated with or endorsed by TSETMC or the Tehran Securities Exchange Technology Management Co.
It is read-only and uses the endpoints of the tsetmc.com web app, which can change without notice. Data is
informational and may be delayed. Nothing here is financial advice.

## Author

<a href="https://www.linkedin.com/in/sepehr-radmard"><img src="https://raw.githubusercontent.com/sepehr071/iran-mcp/main/assets/author-banner.png" alt="Sepehr Radmard: open-source MCP servers for the Iranian web. LinkedIn: linkedin.com/in/sepehr-radmard" width="100%"></a>

Built and maintained by **Sepehr Radmard** (سپهر رادمرد). Connect on [LinkedIn](https://www.linkedin.com/in/sepehr-radmard) or follow [@sepehr071 on GitHub](https://github.com/sepehr071) for more MCP servers for Iranian websites, all listed in [iran-mcp](https://github.com/sepehr071/iran-mcp). If this saves you time, a star on the repo helps other people find it.

## License

[MIT](https://github.com/sepehr071/tsetmc-mcp/blob/main/LICENSE)
