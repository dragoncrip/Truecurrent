import requests
import time
import statistics
import json
from datetime import datetime, timezone

BASE = "https://sentry.exchange.grpc-web.injective.network/api/exchange/derivative/v1"

def get_markets():
    r = requests.get(f"{BASE}/markets?marketStatus=active", timeout=30)
    r.raise_for_status()
    return [m for m in r.json().get("markets", []) if m.get("isPerpetual")]

def get_funding_rates(market_id, limit=200):
    r = requests.get(
        f"{BASE}/fundingRates",
        params={"marketId": market_id, "limit": limit},
        timeout=30
    )
    r.raise_for_status()
    return r.json().get("fundingRates", [])

def average_7d_annualized(rates):
    if not rates:
        return None
    recent = rates[:168]
    hourly = [float(r["rate"]) for r in recent]
    avg = statistics.mean(hourly)
    return round(avg * 8760 * 100, 2)

def main():
    markets = get_markets()
    results = []

    for m in markets:
        try:
            rates = get_funding_rates(m["marketId"])
            avg_7d = average_7d_annualized(rates)

            # Funding actual (último rate)
            last_rate_str = m.get("perpetualMarketFunding", {}).get("lastFundingRate")
            current_annualized = None
            if last_rate_str:
                current_annualized = round(float(last_rate_str) * 8760 * 100, 2)

            # 24h change (placeholder - Chronos no siempre es público)
            price_change_24h = None  # puedes expandir después si encuentras el endpoint

            if avg_7d is not None:
                results.append({
                    "ticker": m["ticker"],
                    "marketId": m["marketId"],
                    "avg_7d_annualized_%": avg_7d,
                    "current_funding_annualized_%": current_annualized,
                    "price_change_24h_%": price_change_24h
                })
        except Exception as e:
            print(f"Error en {m['ticker']}: {e}")
        time.sleep(0.12)

    results.sort(key=lambda x: abs(x["avg_7d_annualized_%"]), reverse=True)

    output = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(results),
        "data": results
    }

    with open("funding_7d.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"Listo: {len(results)} mercados")

if __name__ == "__main__":
    main()
