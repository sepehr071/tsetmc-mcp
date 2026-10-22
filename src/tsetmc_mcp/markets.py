"""TSETMC tools: symbol search, quotes, market movers, order book, daily history, real vs legal trading, indices."""

from __future__ import annotations

import asyncio
from typing import Annotated, Any, Literal
from urllib.parse import quote

from pydantic import Field

from .http import API, ApiError, fetch
from .registry import tool

# The site stores Arabic letters (ي ك) and may show Persian or Arabic-Indic digits; answers use the Persian forms.
_FA = str.maketrans("يكىۀ٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "یکیه" + "0123456789" * 2)
# market -> (paperTypes value, instrument types `yVal`). Some backends filter by paperTypes and send no `yVal`; others
# ignore paperTypes, answer with every market and add `yVal`, so rows are also filtered by it when present.
MARKETS = {"bourse": (1, {300}), "farabourse": (2, {303}), "rights": (4, {400, 403}), "bonds": (5, {306, 706})}


def fa(s: Any) -> str:
    """Persian-normalise display text (Arabic ي/ك to ی/ک, digits to ASCII)."""
    return str(s or "").translate(_FA).strip()


def _key(s: Any) -> str:
    """Matching key: normalised, lower-case, without spaces, dots and ZWNJ."""
    return "".join(c for c in fa(s).lower() if c not in " .\u200c-")


def _date(d: Any) -> str | None:
    d = int(d or 0)
    return f"{d // 10000:04d}-{d // 100 % 100:02d}-{d % 100:02d}" if d else None


def _time(h: Any) -> str | None:
    h = int(h or 0)
    return f"{h // 10000:02d}:{h // 100 % 100:02d}:{h % 100:02d}" if h else None


def _pct(now: float | None, base: float | None) -> float | None:
    return round((now - base) / base * 100, 2) if now and base else None


def _num(x: Any) -> int | float | None:
    """JSON floats such as 4220.0 become ints; None stays None."""
    return None if x is None else int(x) if float(x).is_integer() else round(float(x), 4)


async def _search(query: str) -> list[dict[str, Any]]:
    q = fa(query)
    if not q:
        raise ApiError("Empty symbol or query. Pass a ticker or name, e.g. 'فولاد'.")
    return (await fetch(f"{API}/Instrument/GetInstrumentSearch/{quote(q, safe='')}"))["instrumentSearch"]


async def _resolve(symbol: str) -> tuple[str, str | None]:
    """Turn a ticker, company name or numeric insCode into (insCode, ticker or None)."""
    s = fa(symbol)
    if s.isdigit() and len(s) >= 10:
        return s, None
    hits = await _search(s)
    k = _key(s)
    for field in ("lVal18AFC", "lVal30"):
        for h in hits:
            if _key(h[field]) == k:
                return h["insCode"], fa(h["lVal18AFC"])
    if len(hits) == 1:
        return hits[0]["insCode"], fa(hits[0]["lVal18AFC"])
    if not hits:
        raise ApiError(f"No instrument matches '{symbol}'. Try another spelling with ts_search_symbols.")
    names = ", ".join(f"{fa(h['lVal18AFC'])} ({fa(h['lVal30'])})" for h in hits[:6])
    raise ApiError(f"'{symbol}' is ambiguous: {names}. Pass the exact ticker or its ins_code from ts_search_symbols.")


@tool("Search symbols")
async def ts_search_symbols(
    query: Annotated[
        str,
        Field(
            min_length=1,
            description="Ticker or company name, Persian (Arabic ي/ك accepted), e.g. 'فولاد', 'خودرو', 'بانک ملت'.",
        ),
    ],
    limit: Annotated[int, Field(ge=1, le=30, description="Max matches (1-30).")] = 10,
) -> dict[str, Any]:
    """Find Tehran Stock Exchange instruments (shares, funds, rights, bonds) by ticker or name.

    Use first when you only have a name. Pass a result's `symbol` (or `ins_code`) to the other ts_ tools.
    An empty list means no match: retry with a shorter name or the other spelling.
    """
    hits = await _search(query)
    return {
        "total": len(hits),
        "matches": [
            {
                "symbol": fa(h["lVal18AFC"]),
                "name": fa(h["lVal30"]),
                "ins_code": h["insCode"],
                "market": fa(h.get("flowTitle")),
                "board": fa(h.get("cgrValCotTitle")),
            }
            for h in hits[:limit]
        ],
    }


@tool("Stock quote")
async def ts_get_quote(
    symbol: Annotated[
        str, Field(min_length=1, description="Ticker or exact name, e.g. 'فولاد', 'وبملت', or a numeric ins_code.")
    ],
) -> dict[str, Any]:
    """Latest price, daily range, volume and key facts of one instrument on the Tehran Stock Exchange.

    `last` is the last trade, `close` the closing (volume-weighted) price; `change_pct` is last vs yesterday's close.
    Prices are in Rial. Use ts_order_book for bids and asks, ts_price_history for earlier days.
    """
    ins, _ = await _resolve(symbol)
    info, cp = await asyncio.gather(
        fetch(f"{API}/Instrument/GetInstrumentInfo/{ins}"), fetch(f"{API}/ClosingPrice/GetClosingPriceInfo/{ins}")
    )
    i, c = info["instrumentInfo"], cp["closingPriceInfo"]
    last, close, yest = c["pDrCotVal"] or None, c["pClosing"] or None, c["priceYesterday"] or None
    th = i.get("staticThreshold") or {}
    return {
        "symbol": fa(i["lVal18AFC"]),
        "name": fa(i["lVal30"]),
        "ins_code": ins,
        "isin": i.get("instrumentID"),
        "market": fa(i.get("flowTitle")),
        "sector": fa((i.get("sector") or {}).get("lSecVal")),
        "status": fa((c.get("instrumentState") or {}).get("cEtavalTitle")),
        "unit": "rial",
        "date": _date(c["dEven"]),
        "time": _time(c["hEven"]),
        "last": _num(last),
        "close": _num(close),
        "yesterday": _num(yest),
        "open": _num(c["priceFirst"]),
        "low": _num(c["priceMin"]),
        "high": _num(c["priceMax"]),
        "change_pct": _pct(last, yest),
        "close_change_pct": _pct(close, yest),
        "volume": _num(c["qTotTran5J"]),
        "trades": _num(c["zTotTran"]),
        "value": _num(c["qTotCap"]),
        "allowed_min": _num(th.get("psGelStaMin")),
        "allowed_max": _num(th.get("psGelStaMax")),
        "week_low": _num(i.get("minWeek")),
        "week_high": _num(i.get("maxWeek")),
        "year_low": _num(i.get("minYear")),
        "year_high": _num(i.get("maxYear")),
        "shares": _num(i.get("zTitad")),
        "market_cap": _num(close * i["zTitad"]) if close and i.get("zTitad") else None,
        "sector_pe": (i.get("eps") or {}).get("sectorPE"),
    }


@tool("Market movers")
async def ts_market_movers(
    market: Annotated[
        Literal["bourse", "farabourse", "rights", "bonds"],
        Field(
            description="bourse = Tehran Stock Exchange shares, farabourse = Iran Fara Bourse shares, rights = rights issues, bonds."
        ),
    ] = "bourse",
    sort_by: Annotated[
        Literal["gain", "loss", "volume", "value", "trades"],
        Field(
            description="gain/loss = biggest last-trade change vs yesterday, volume = shares traded, value = Rial traded, trades = trade count."
        ),
    ] = "gain",
    limit: Annotated[int, Field(ge=1, le=30, description="Max rows (30 keeps the reply under 15 KB).")] = 10,
) -> dict[str, Any]:
    """Top traded instruments of a market today, ranked by gain, loss, volume, value or trade count.

    Only instruments that traded are listed. `limit_up`/`limit_down` marks a price stuck at its daily limit.
    Prices are in Rial. Pass a row's `symbol` to ts_get_quote or ts_order_book.
    """
    params = {
        "market": 0,
        "paperTypes[0]": MARKETS[market][0],
        "showTraded": "true",
        "withBestLimits": "false",
        "hEven": 0,
        "RefID": 0,
    }
    watch = (await fetch(f"{API}/ClosingPrice/GetMarketWatch", params))["marketwatch"]
    rows = [r for r in watch if r["pdv"] and r.get("yVal", 0) in MARKETS[market][1] | {0}]
    pct = lambda r: _pct(r["pdv"], r["py"]) or 0.0  # noqa: E731
    sort_key = {
        "gain": lambda r: -pct(r),
        "loss": pct,
        "volume": lambda r: -r["qtj"],
        "value": lambda r: -r["qtc"],
        "trades": lambda r: -r["ztt"],
    }[sort_by]
    out = []
    for r in sorted(rows, key=sort_key)[:limit]:
        o = {
            "symbol": fa(r["lva"]),
            "name": fa(r["lvc"]),
            "ins_code": r["insCode"],
            "last": _num(r["pdv"]),
            "close": _num(r["pcl"]),
            "yesterday": _num(r["py"]),
            "change_pct": _pct(r["pdv"], r["py"]),
            "low": _num(r["pmn"]),
            "high": _num(r["pmx"]),
            "volume": _num(r["qtj"]),
            "trades": _num(r["ztt"]),
            "value": _num(r["qtc"]),
            "time": _time(r["hEven"]),
        }
        if r["pdv"] >= r["pMax"]:
            o["limit_up"] = True
        elif r["pdv"] <= r["pMin"]:
            o["limit_down"] = True
        out.append(o)
    return {"market": market, "sorted_by": sort_by, "traded_count": len(rows), "unit": "rial", "rows": out}


@tool("Order book")
async def ts_order_book(
    symbol: Annotated[
        str, Field(min_length=1, description="Ticker or exact name, e.g. 'فولاد', or a numeric ins_code.")
    ],
) -> dict[str, Any]:
    """Best five bid and ask levels (price, volume, order count) of one instrument.

    Empty outside trading hours. A level with ask price 0 means a buy queue (no sellers), bid price 0 a sell queue.
    Prices are in Rial.
    """
    ins, ticker = await _resolve(symbol)
    levels = (await fetch(f"{API}/BestLimits/{ins}"))["bestLimits"]
    out: dict[str, Any] = {
        "symbol": ticker,
        "ins_code": ins,
        "unit": "rial",
        "levels": [
            {
                "level": b["number"],
                "bid_price": _num(b["pMeDem"]),
                "bid_volume": _num(b["qTitMeDem"]),
                "bid_orders": b["zOrdMeDem"],
                "ask_price": _num(b["pMeOf"]),
                "ask_volume": _num(b["qTitMeOf"]),
                "ask_orders": b["zOrdMeOf"],
            }
            for b in levels
        ],
    }
    if not levels:
        out["note"] = "No open order book now (market closed, or the instrument did not trade today)."
    return out


@tool("Daily price history")
async def ts_price_history(
    symbol: Annotated[
        str, Field(min_length=1, description="Ticker or exact name, e.g. 'فولاد', or a numeric ins_code.")
    ],
    days: Annotated[
        int, Field(ge=1, le=50, description="Latest trading days to return (50 keeps the reply under 15 KB).")
    ] = 20,
) -> dict[str, Any]:
    """Daily open, high, low, close, volume, trades and value of one instrument for its latest trading days, newest first.

    Prices are in Rial and not adjusted for capital increases or dividends; dates are Gregorian.
    """
    ins, ticker = await _resolve(symbol)
    rows = (await fetch(f"{API}/ClosingPrice/GetClosingPriceDailyList/{ins}/{days}"))["closingPriceDaily"]
    return {
        "symbol": ticker,
        "ins_code": ins,
        "unit": "rial",
        "rows": [
            {
                "date": _date(r["dEven"]),
                "open": _num(r["priceFirst"]),
                "high": _num(r["priceMax"]),
                "low": _num(r["priceMin"]),
                "close": _num(r["pClosing"]),
                "last": _num(r["pDrCotVal"]),
                "yesterday": _num(r["priceYesterday"]),
                "change_pct": _pct(r["pDrCotVal"], r["priceYesterday"]),
                "volume": _num(r["qTotTran5J"]),
                "trades": _num(r["zTotTran"]),
                "value": _num(r["qTotCap"]),
            }
            for r in rows
        ],
    }


@tool("Real vs legal trading")
async def ts_real_legal(
    symbol: Annotated[
        str, Field(min_length=1, description="Ticker or exact name, e.g. 'فولاد', or a numeric ins_code.")
    ],
    days: Annotated[
        int, Field(ge=1, le=10, description="Latest trading days to return (1-10; each day is one upstream call).")
    ] = 3,
) -> dict[str, Any]:
    """Buy and sell volume, value and buyer/seller counts split by real (individual) and legal (institutional) traders per day.

    `net_real_volume` > 0 means individuals bought more than they sold (money flowing in from real investors).
    Newest day first. Volumes are in shares, values in Rial.
    """
    ins, ticker = await _resolve(symbol)
    dates = [
        r["dEven"]
        for r in (await fetch(f"{API}/ClosingPrice/GetClosingPriceDailyList/{ins}/{days}"))["closingPriceDaily"]
    ]
    results = await asyncio.gather(
        *(fetch(f"{API}/ClientType/GetClientTypeHistory/{ins}/{d}") for d in dates), return_exceptions=True
    )
    rows, missing = [], []
    for d, res in zip(dates, results, strict=True):
        c = None if isinstance(res, BaseException) else res.get("clientType")
        if not c:
            missing.append(_date(d))
            continue
        rows.append(
            {
                "date": _date(d),
                "real_buy_volume": _num(c["buy_I_Volume"]),
                "real_sell_volume": _num(c["sell_I_Volume"]),
                "legal_buy_volume": _num(c["buy_N_Volume"]),
                "legal_sell_volume": _num(c["sell_N_Volume"]),
                "net_real_volume": _num(c["buy_I_Volume"] - c["sell_I_Volume"]),
                "real_buy_value": _num(c["buy_I_Value"]),
                "real_sell_value": _num(c["sell_I_Value"]),
                "legal_buy_value": _num(c["buy_N_Value"]),
                "legal_sell_value": _num(c["sell_N_Value"]),
                "real_buyers": _num(c["buy_I_Count"]),
                "real_sellers": _num(c["sell_I_Count"]),
                "legal_buyers": _num(c["buy_N_Count"]),
                "legal_sellers": _num(c["sell_N_Count"]),
            }
        )
    return {"symbol": ticker, "ins_code": ins, "unit": "rial", "rows": rows, "unavailable_dates": missing}


async def _indices() -> list[dict[str, Any]]:
    return (await fetch(f"{API}/Index/GetIndexB1LastAll/All/1"))["indexB1"]


@tool("Market indices")
async def ts_indices(
    query: Annotated[
        str | None,
        Field(description="Optional part of an index name, e.g. 'بانک', 'خودرو', 'شاخص کل', 'هم وزن'. Omit for all."),
    ] = None,
    limit: Annotated[int, Field(ge=1, le=60, description="Max indices, strongest change first.")] = 60,
) -> dict[str, Any]:
    """TSE total index, market state and trading totals, plus every sector and market index with its change.

    Use to see which sectors lead or lag today. Pass an index `name` to ts_index_history for its past values.
    """
    overview, idx = await asyncio.gather(fetch(f"{API}/MarketData/GetMarketOverview/1"), _indices())
    o = overview["marketOverview"]
    k = _key(query or "")
    rows = [x for x in idx if k in _key(x["lVal30"])]
    rows.sort(key=lambda x: -x["xVarIdxJRfV"])
    return {
        "market": {
            "state": fa(o["marketStateTitle"]),
            "date": _date(o["marketActivityDEven"]),
            "time": _time(o["marketActivityHEven"]),
            "total_index": _num(o["indexLastValue"]),
            "total_index_change": _num(o["indexChange"]),
            "total_index_change_pct": _pct(o["indexLastValue"], o["indexLastValue"] - o["indexChange"]),
            "equal_weight_index": _num(o["indexEqualWeightedLastValue"]),
            "equal_weight_change": _num(o["indexEqualWeightedChange"]),
            "trades": _num(o["marketActivityZTotTran"]),
            "volume": _num(o["marketActivityQTotTran"]),
            "value": _num(o["marketActivityQTotCap"]),
            "market_value": _num(o["marketValue"]),
        },
        "indices": [
            {
                "name": fa(x["lVal30"]),
                "ins_code": x["insCode"],
                "value": _num(x["xDrNivJIdx004"]),
                "change": _num(x["indexChange"]),
                "change_pct": x["xVarIdxJRfV"],
                "high": _num(x["xPhNivJIdx004"]),
                "low": _num(x["xPbNivJIdx004"]),
            }
            for x in rows[:limit]
        ],
    }


@tool("Index history")
async def ts_index_history(
    index: Annotated[
        str,
        Field(
            min_length=1,
            description="Index name or part of it (default total index), e.g. 'شاخص کل', 'بانک', 'خودرو', or a numeric ins_code.",
        ),
    ] = "شاخص کل",
    days: Annotated[int, Field(ge=1, le=100, description="Latest trading days to return (1-100).")] = 30,
) -> dict[str, Any]:
    """Daily close, high, low and percent change of a TSE index (total, equal-weight, sector...), newest first.

    Find index names with ts_indices.
    """
    s = fa(index)
    name = None
    if s.isdigit() and len(s) >= 10:
        code = s
    else:
        k = _key(s)
        idx = await _indices()
        hits = [x for x in idx if _key(x["lVal30"]) == k] or [x for x in idx if k in _key(x["lVal30"])]
        if len(hits) != 1:
            names = ", ".join(fa(x["lVal30"]) for x in (hits or idx)[:8])
            raise ApiError(
                f"Index '{index}' is ambiguous or unknown: {names}. Use a name from ts_indices."
                if hits
                else f"No index matches '{index}'. Use a name from ts_indices, e.g. {names}."
            )
        code, name = hits[0]["insCode"], fa(hits[0]["lVal30"])
    rows = (await fetch(f"{API}/Index/GetIndexB2History/{code}"))["indexB2"][-(days + 1) :]
    out = []
    for prev, r in zip(rows, rows[1:], strict=False):
        out.append(
            {
                "date": _date(r["dEven"]),
                "close": r["xNivInuClMresIbs"],
                "high": r["xNivInuPhMresIbs"],
                "low": r["xNivInuPbMresIbs"],
                "change_pct": _pct(r["xNivInuClMresIbs"], prev["xNivInuClMresIbs"]),
            }
        )
    return {"index": name, "ins_code": code, "rows": out[::-1]}
