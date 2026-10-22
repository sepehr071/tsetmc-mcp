import httpx
import pytest
from conftest import fixture

from tsetmc_mcp import markets

pytestmark = pytest.mark.anyio

FOOLAD = "46348559193224090"
P = "/api/"


def foolad_routes(api):
    api[P + "Instrument/GetInstrumentSearch/فولاد"] = fixture("search_foolad.json")
    api[P + f"Instrument/GetInstrumentInfo/{FOOLAD}"] = fixture("instrument_info.json")
    api[P + f"ClosingPrice/GetClosingPriceInfo/{FOOLAD}"] = fixture("closing_info.json")


async def test_all_tools_are_read_only(client):
    tools = (await client.list_tools()).tools
    assert {t.name for t in tools} == {
        "ts_search_symbols",
        "ts_get_quote",
        "ts_market_movers",
        "ts_order_book",
        "ts_price_history",
        "ts_real_legal",
        "ts_indices",
        "ts_index_history",
    }
    for t in tools:
        assert t.annotations.read_only_hint is True, t.name
        assert t.description and t.title, t.name


def test_normalisation():
    assert markets.fa("فولاد مباركه اصفهان ١٢٣ ۴") == "فولاد مبارکه اصفهان 123 4"
    assert markets._key("گسترش‌صنايع كشاورزي") == markets._key("گسترش صنایع کشاورزی")
    assert markets._date(20261021) == "2026-10-21" and markets._time(95030) == "09:50:30"


async def test_search_normalises_query_and_output(client, api):
    api[P + "Instrument/GetInstrumentSearch/فولاد"] = fixture("search_foolad.json")
    result = await client.call_tool("ts_search_symbols", {"query": "فولاد", "limit": 2})
    m = result.structured_content["matches"]
    assert len(m) == 2 and m[0]["symbol"] == "فولاد" and m[0]["name"] == "فولاد مبارکه اصفهان"
    assert m[0]["ins_code"] == FOOLAD


async def test_quote(client, api):
    foolad_routes(api)
    q = (await client.call_tool("ts_get_quote", {"symbol": "فولاد"})).structured_content
    assert q["symbol"] == "فولاد" and q["ins_code"] == FOOLAD and q["unit"] == "rial"
    assert q["last"] == 4230 and q["close"] == 4220 and q["yesterday"] == 4340
    assert q["change_pct"] == pytest.approx(-2.53, abs=0.01)
    assert q["date"] == "2026-10-21" and q["time"] == "12:30:02"
    assert q["market_cap"] == 4220 * 1935000000000
    assert q["allowed_min"] == 4210 and q["year_high"] == 4540


async def test_quote_by_ins_code_skips_search(client, api):
    foolad_routes(api)
    await client.call_tool("ts_get_quote", {"symbol": FOOLAD})
    assert not any("GetInstrumentSearch" in str(r.url) for r in api.calls)


async def test_unknown_symbol_is_an_error(client, api):
    api[P + "Instrument/GetInstrumentSearch/نامعتبر"] = {"instrumentSearch": []}
    result = await client.call_tool("ts_get_quote", {"symbol": "نامعتبر"})
    assert result.is_error and "ts_search_symbols" in result.content[0].text


async def test_ambiguous_symbol_lists_candidates(client, api):
    api[P + "Instrument/GetInstrumentSearch/فول"] = fixture("search_foolad.json")
    result = await client.call_tool("ts_get_quote", {"symbol": "فول"})
    assert result.is_error and "ambiguous" in result.content[0].text and "فولاد" in result.content[0].text


async def test_movers(client, api):
    api[P + "ClosingPrice/GetMarketWatch"] = fixture("marketwatch.json")
    gain = (await client.call_tool("ts_market_movers", {"sort_by": "gain", "limit": 3})).structured_content
    pcts = [r["change_pct"] for r in gain["rows"]]
    assert pcts == sorted(pcts, reverse=True) and len(pcts) == 3
    loss = (await client.call_tool("ts_market_movers", {"sort_by": "loss", "limit": 3})).structured_content
    assert loss["rows"][0]["change_pct"] <= pcts[0]
    vol = (await client.call_tool("ts_market_movers", {"sort_by": "value", "limit": 5})).structured_content
    vals = [r["value"] for r in vol["rows"]]
    assert vals == sorted(vals, reverse=True)
    sent = api.calls[0].url.params
    assert sent["paperTypes[0]"] == "1" and sent["showTraded"] == "true" and sent["withBestLimits"] == "false"


async def test_movers_filter_by_market(client, api):
    api[P + "ClosingPrice/GetMarketWatch"] = fixture("marketwatch.json")
    watch = fixture("marketwatch.json")["marketwatch"]
    codes = {m: {r["insCode"] for r in watch if r["yVal"] == y} for m, y in (("bourse", 300), ("farabourse", 303))}
    assert codes["bourse"] and codes["farabourse"]
    for market, expected in codes.items():
        rows = (await client.call_tool("ts_market_movers", {"market": market, "limit": 30})).structured_content["rows"]
        assert rows and {r["ins_code"] for r in rows} <= expected


async def test_movers_without_ytype_trusts_server_filter(client, api):
    watch = fixture("marketwatch.json")
    for r in watch["marketwatch"]:
        del r["yVal"]
    api[P + "ClosingPrice/GetMarketWatch"] = watch
    rows = (await client.call_tool("ts_market_movers", {"market": "farabourse", "limit": 30})).structured_content[
        "rows"
    ]
    assert len(rows) == len([r for r in watch["marketwatch"] if r["pdv"]])
    assert api.calls[0].url.params["paperTypes[0]"] == "2"


async def test_order_book(client, api):
    api[P + f"BestLimits/{FOOLAD}"] = fixture("best_limits.json")
    ob = (await client.call_tool("ts_order_book", {"symbol": FOOLAD})).structured_content
    assert len(ob["levels"]) == 5
    assert ob["levels"][0] == {
        "level": 1,
        "bid_price": 4230,
        "bid_volume": 1382803,
        "bid_orders": 20,
        "ask_price": 4240,
        "ask_volume": 4358512,
        "ask_orders": 17,
    }


async def test_order_book_empty_has_note(client, api):
    api[P + f"BestLimits/{FOOLAD}"] = {"bestLimits": []}
    ob = (await client.call_tool("ts_order_book", {"symbol": FOOLAD})).structured_content
    assert ob["levels"] == [] and "market closed" in ob["note"]


async def test_price_history(client, api):
    api[P + f"ClosingPrice/GetClosingPriceDailyList/{FOOLAD}/6"] = fixture("daily_list.json")
    rows = (await client.call_tool("ts_price_history", {"symbol": FOOLAD, "days": 6})).structured_content["rows"]
    assert len(rows) == 6 and rows[0]["date"] == "2026-10-21"
    assert rows[0]["close"] == 4220 and rows[0]["high"] == 4340 and rows[0]["volume"] == 4864252101


async def test_real_legal(client, api):
    api[P + f"ClosingPrice/GetClosingPriceDailyList/{FOOLAD}/2"] = {
        "closingPriceDaily": [{"dEven": 20261021}, {"dEven": 20261020}, {"dEven": 20261019}][:2]
    }
    api[P + f"ClientType/GetClientTypeHistory/{FOOLAD}/20261021"] = fixture("client_type_0.json")
    api[P + f"ClientType/GetClientTypeHistory/{FOOLAD}/20261020"] = lambda r: httpx.Response(500, text="")
    result = (await client.call_tool("ts_real_legal", {"symbol": FOOLAD, "days": 2})).structured_content
    row = result["rows"][0]
    assert row["date"] == "2026-10-21" and row["net_real_volume"] == 1177317761 - 3946121693
    assert row["legal_buy_volume"] == 3686934340
    assert result["unavailable_dates"] == ["2026-10-20"]


async def test_indices(client, api):
    api[P + "MarketData/GetMarketOverview/1"] = fixture("market_overview.json")
    api[P + "Index/GetIndexB1LastAll/All/1"] = fixture("index_b1.json")
    r = (await client.call_tool("ts_indices", {})).structured_content
    assert r["market"]["total_index"] == 8173767.36 and r["market"]["state"] == "بسته"
    assert r["market"]["total_index_change_pct"] == pytest.approx(-1.19, abs=0.01)
    pcts = [i["change_pct"] for i in r["indices"]]
    assert pcts == sorted(pcts, reverse=True)
    one = (await client.call_tool("ts_indices", {"query": "شاخص كل"})).structured_content["indices"]
    assert {i["name"] for i in one} == {"شاخص کل", "شاخص کل (هم وزن)"}


async def test_index_history(client, api):
    api[P + "Index/GetIndexB1LastAll/All/1"] = fixture("index_b1.json")
    api[P + "Index/GetIndexB2History/32097828799138957"] = fixture("index_b2.json")
    r = (await client.call_tool("ts_index_history", {"days": 3})).structured_content
    assert r["index"] == "شاخص کل" and len(r["rows"]) == 3
    assert r["rows"][0]["date"] > r["rows"][1]["date"] and "change_pct" in r["rows"][0]


async def test_index_history_unknown(client, api):
    api[P + "Index/GetIndexB1LastAll/All/1"] = fixture("index_b1.json")
    result = await client.call_tool("ts_index_history", {"index": "هیچی"})
    assert result.is_error and "ts_indices" in result.content[0].text


async def test_blank_and_slash_queries(client, api):
    blank = await client.call_tool("ts_search_symbols", {"query": "  "})
    assert blank.is_error and "Empty" in blank.content[0].text and not api.calls
    api[P + "Instrument/GetInstrumentSearch/a/b"] = {"instrumentSearch": []}
    await client.call_tool("ts_search_symbols", {"query": "a/b"})
    assert "GetInstrumentSearch/a%2Fb" in str(api.calls[-1].url)


async def test_persian_digit_ins_code_skips_search(client, api):
    foolad_routes(api)
    await client.call_tool("ts_get_quote", {"symbol": "۴۶۳۴۸۵۵۹۱۹۳۲۲۴۰۹۰"})
    assert not any("GetInstrumentSearch" in str(r.url) for r in api.calls)
    assert any(FOOLAD in str(r.url) for r in api.calls)
