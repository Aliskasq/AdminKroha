#!/usr/bin/env python3
"""
Fetch historical price from Binance for any symbol at a specific timestamp.

Usage:
    python get_historical_price.py BTCUSDT "2026-07-03 14:30:00"
    python get_historical_price.py ETHUSDT "2026-07-03 14:30:00" --interval 1m
    python get_historical_price.py SOLUSDT --days-ago 120 --time "14:30:00"
"""

import argparse
import sys
from datetime import datetime, timedelta, timezone
from typing import Optional

import requests


BINANCE_KLINES_URL = "https://api.binance.com/api/v3/klines"


def parse_datetime(dt_str: str, time_str: Optional[str] = None) -> datetime:
    """Parse date/time string to UTC datetime."""
    if time_str:
        # Combine date and time
        dt = datetime.strptime(f"{dt_str} {time_str}", "%Y-%m-%d %H:%M:%S")
    else:
        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
    return dt.replace(tzinfo=timezone.utc)


def get_price_at_time(
    symbol: str,
    target_dt: datetime,
    interval: str = "1m"
) -> Optional[dict]:
    """
    Fetch kline (candlestick) for symbol at target datetime.

    Returns dict with open, high, low, close, volume, timestamp.
    """
    # Convert to milliseconds
    start_ms = int(target_dt.timestamp() * 1000)
    end_ms = start_ms + 60_000  # 1 minute window

    params = {
        "symbol": symbol.upper(),
        "interval": interval,
        "startTime": start_ms,
        "endTime": end_ms,
        "limit": 1
    }

    try:
        response = requests.get(BINANCE_KLINES_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data:
            return None

        kline = data[0]
        return {
            "symbol": symbol.upper(),
            "timestamp": datetime.fromtimestamp(kline[0] / 1000, tz=timezone.utc),
            "open": float(kline[1]),
            "high": float(kline[2]),
            "low": float(kline[3]),
            "close": float(kline[4]),
            "volume": float(kline[5]),
            "close_time": datetime.fromtimestamp(kline[6] / 1000, tz=timezone.utc),
            "quote_volume": float(kline[7]),
            "trades": int(kline[8]),
        }
    except requests.RequestException as e:
        print(f"❌ Request error: {e}", file=sys.stderr)
        return None
    except (ValueError, IndexError) as e:
        print(f"❌ Parse error: {e}", file=sys.stderr)
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Get historical price from Binance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Exact timestamp
  python get_historical_price.py BTCUSDT "2026-07-03 14:30:00"

  # 4 months ago (120 days) at specific time today
  python get_historical_price.py ETHUSDT --days-ago 120 --time "14:30:00"

  # Different interval (1h, 4h, 1d)
  python get_historical_price.py SOLUSDT "2026-07-03 14:30:00" --interval 1h
        """
    )

    parser.add_argument("symbol", help="Trading pair (e.g., BTCUSDT, ETHUSDT)")
    parser.add_argument("datetime", nargs="?", help="Target datetime UTC: 'YYYY-MM-DD HH:MM:SS'")
    parser.add_argument("--days-ago", type=int, help="Days ago from now (e.g., 120 for ~4 months)")
    parser.add_argument("--time", default="00:00:00", help="Time of day UTC (HH:MM:SS) when using --days-ago")
    parser.add_argument("--interval", default="1m",
                        choices=["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w", "1M"],
                        help="Kline interval (default: 1m)")

    args = parser.parse_args()

    # Determine target datetime
    if args.days_ago:
        target_date = datetime.now(timezone.utc) - timedelta(days=args.days_ago)
        target_dt = parse_datetime(target_date.strftime("%Y-%m-%d"), args.time)
        print(f"📅 Target: {args.days_ago} days ago at {args.time} UTC → {target_dt.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    elif args.datetime:
        target_dt = parse_datetime(args.datetime)
        print(f"📅 Target: {target_dt.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    else:
        parser.error("Provide either DATETIME or --days-ago")
        return 1

    print(f"🔍 Fetching {args.symbol.upper()} @ {args.interval}...")

    result = get_price_at_time(args.symbol, target_dt, args.interval)

    if result is None:
        print(f"❌ No data for {args.symbol.upper()} at {target_dt} (interval={args.interval})")
        print("   Try a different interval (e.g., 1h, 1d) or check symbol spelling.")
        return 1

    print(f"\n✅ Price data for {result['symbol']} at {result['timestamp'].strftime('%Y-%m-%d %H:%M:%S %Z')}:")
    print(f"   Open:   ${result['open']:,.8f}")
    print(f"   High:   ${result['high']:,.8f}")
    print(f"   Low:    ${result['low']:,.8f}")
    print(f"   Close:  ${result['close']:,.8f}  ← Цена в момент времени")
    print(f"   Volume: {result['volume']:,.4f} {result['symbol'].replace('USDT', '')}")
    print(f"   Trades: {result['trades']:,}")

    return 0


if __name__ == "__main__":
    sys.exit(main())