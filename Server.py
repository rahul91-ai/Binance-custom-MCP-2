import os
import requests
from fastmcp import FastMCP

mcp = FastMCP("Binance Futures MCP")

BASE_URL = "https://fapi.binance.com"
TIMEOUT = 15


def binance_get(path, params=None):
    """Request public Binance USDⓈ-M Futures market data."""
    response = requests.get(
        f"{BASE_URL}{path}",
        params=params,
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


@mcp.tool()
def list_usdt_perpetuals():
    """List active USDT-settled Binance USDⓈ-M perpetual contracts."""
    data = binance_get("/fapi/v1/exchangeInfo")
    return [
        {
            "symbol": item["symbol"],
            "status": item["status"],
            "baseAsset": item["baseAsset"],
            "quoteAsset": item["quoteAsset"],
            "contractType": item["contractType"],
        }
        for item in data["symbols"]
        if item.get("status") == "TRADING"
        and item.get("quoteAsset") == "USDT"
        and item.get("contractType") == "PERPETUAL"
    ]


@mcp.tool()
def get_futures_price(symbol: str):
    """Get the current price for a Binance USDⓈ-M Futures symbol, e.g. BTCUSDT."""
    symbol = symbol.upper().strip()
    data = binance_get("/fapi/v1/ticker/price", {"symbol": symbol})
    return data


@mcp.tool()
def get_futures_klines(
    symbol: str,
    interval: str = "1h",
    limit: int = 500,
):
    """Get Binance Futures candles. Supported limits are 1 to 1500."""
    symbol = symbol.upper().strip()
    allowed_intervals = {
        "1m", "3m", "5m", "15m", "30m",
        "1h", "2h", "4h", "6h", "8h", "12h",
        "1d", "3d", "1w", "1M",
    }

    if interval not in allowed_intervals:
        return {"error": "Unsupported interval."}

    if not 1 <= limit <= 1500:
        return {"error": "Limit must be between 1 and 1500."}

    rows = binance_get(
        "/fapi/v1/klines",
        {"symbol": symbol, "interval": interval, "limit": limit},
    )

    return [
        {
            "open_time": row[0],
            "open": row[1],
            "high": row[2],
            "low": row[3],
            "close": row[4],
            "volume": row[5],
            "close_time": row[6],
            "quote_volume": row[7],
            "trades": row[8],
            "taker_buy_base_volume": row[9],
            "taker_buy_quote_volume": row[10],
        }
        for row in rows
    ]


@mcp.tool()
def get_futures_order_book(symbol: str, limit: int = 20):
    """Get the Binance Futures order book for a symbol."""
    symbol = symbol.upper().strip()
    allowed_limits = {5, 10, 20, 50, 100, 500, 1000}

    if limit not in allowed_limits:
        return {
            "error": "Limit must be one of 5, 10, 20, 50, 100, 500, or 1000."
        }

    return binance_get(
        "/fapi/v1/depth",
        {"symbol": symbol, "limit": limit},
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=port,
    )
