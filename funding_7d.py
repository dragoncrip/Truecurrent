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

            # Funding actual
            last_rate_str = m.get("perpetualMarketFunding", {}).get("lastFundingRate")
            current_annualized = None
            if last_rate_str:
                current_annualized = round(float(last_rate_str) * 8760 * 100, 2)

            # Cambio 24h (por ahora None)
            price_change_24h = None

            if avg_7d is not None:
                # Clasificación CRYPTO / RWA
                oracle_type = m.get("oracleType", "").lower()
                ticker_upper = m["ticker"].upper()

                is_rwa = (
                    oracle_type == "pythpro" or
                    any(x in ticker_upper for x in [
                        "AAPL", "NVDA", "TSLA", "MSFT", "META", "AMZN", "GOOGL", "NFLX",
                        "MSTR", "COIN", "HOOD", "CRCL", "TRADFI", "TTI", "AIX", "SPCX",
                        "XAU", "XAG", "WTI", "EURUSD"
                    ])
                )

                results.append({
                    "ticker": m["ticker"],
                    "marketId": m["marketId"],
                    "type": "RWA" if is_rwa else "CRYPTO",
                    "avg_7d_annualized_%": avg_7d,
                    "current_funding_annualized_%": current_annualized,
                    "price_change_24h_%": price_change_24h
                })

        except Exception as e:
            print(f"Error en {m.get('ticker', 'unknown')}: {e}")

        time.sleep(0.12)

    results.sort(key=lambda x: abs(x["avg_7d_annualized_%"]), reverse=True)

    output = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(results),
        "data": results
    }

    with open("funding_7d.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"Listo: {len(results)} mercados guardados en funding_7d.json")

if __name__ == "__main__":
    main()
