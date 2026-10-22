import pytest

pytestmark = [pytest.mark.live, pytest.mark.anyio]


async def test_live_search(client):
    result = await client.call_tool("ts_search_symbols", {"query": "فولاد", "limit": 3})
    assert result.structured_content["matches"][0]["symbol"] == "فولاد"


async def test_live_quote(client):
    q = (await client.call_tool("ts_get_quote", {"symbol": "فولاد"})).structured_content
    assert q["ins_code"] == "46348559193224090" and q["close"] > 0 and q["shares"] > 0


async def test_live_quote_arabic_letters(client):
    q = (await client.call_tool("ts_get_quote", {"symbol": "تكشا"})).structured_content
    assert q["symbol"] == "تکشا"


async def test_live_movers(client):
    result = await client.call_tool("ts_market_movers", {"sort_by": "value", "limit": 5})
    rows = result.structured_content["rows"]
    assert len(rows) == 5 and rows[0]["value"] >= rows[-1]["value"]
    assert len(result.content[0].text) < 15_000


async def test_live_order_book(client):
    ob = (await client.call_tool("ts_order_book", {"symbol": "فولاد"})).structured_content
    assert "levels" in ob


async def test_live_price_history(client):
    result = await client.call_tool("ts_price_history", {"symbol": "فولاد", "days": 50})
    assert len(result.structured_content["rows"]) == 50
    assert len(result.content[0].text) < 15_000


async def test_live_real_legal(client):
    result = await client.call_tool("ts_real_legal", {"symbol": "فولاد", "days": 3})
    assert result.structured_content["rows"]


async def test_live_indices(client):
    result = await client.call_tool("ts_indices", {})
    assert result.structured_content["market"]["total_index"] > 0
    assert len(result.structured_content["indices"]) > 30
    assert len(result.content[0].text) < 15_000


async def test_live_index_history(client):
    total = (await client.call_tool("ts_index_history", {"days": 100})).structured_content
    assert len(total["rows"]) == 100 and len(total["rows"][0]) == 5
    sector = (await client.call_tool("ts_index_history", {"index": "بانک", "days": 5})).structured_content
    assert sector["rows"]
