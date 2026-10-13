import requests
import time
import statistics
import json
from datetime import datetime

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
    return round(avg * 8760 * 100, 2)  # % anualizado

def main():
    markets = get_markets()
    results = []

    for m in markets:
        try:
            rates = get_funding_rates(m["marketId"])
            avg = average_7d_annualized(rates)
            if avg is not None:
                results.append({
                    "ticker": m["ticker"],
                    "marketId": m["marketId"],
                    "avg_7d_annualized_%": avg,
                    "samples": min(len(rates), 168)
                })
        except Exception as e:
            print(f"Error en {m['ticker']}: {e}")
        time.sleep(0.12)  # evita rate limit

    results.sort(key=lambda x: abs(x["avg_7d_annualized_%"]), reverse=True)

    output = {
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "count": len(results),
        "data": results
    }

    with open("funding_7d.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"Listo: {len(results)} mercados guardados en funding_7d.json")

if __name__ == "__main__":
    main()
