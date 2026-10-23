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

def average_annualized(rates, hours):
    if not rates:
        return None
    recent = rates[:hours]
    hourly = [float(r["rate"]) for r in recent]
    if not hourly:
        return None
    avg = statistics.mean(hourly)
    return round(avg * 8760 * 100, 2)

def calculate_stability_and_score(avg_7d, avg_3d, avg_24h, current):
    values = [avg_7d, avg_3d, avg_24h, current]
    valid = [v for v in values if v is not None]
    
    if len(valid) < 2:
        return 0, 0.0
    
    abs_values = [abs(v) for v in valid]
    mean_abs = statistics.mean(abs_values)
    
    if mean_abs == 0:
        return 50, 0.0
    
    std_abs = statistics.pstdev(abs_values) if len(abs_values) > 1 else 0
    rel_std = std_abs / mean_abs
    
    # Estabilidad base (menor variación relativa = más estable)
    stability = max(0, min(100, round(100 - rel_std * 70)))
    
    # Bonus si todos tienen el mismo signo
    signs = [1 if v >= 0 else -1 for v in valid]
    if len(set(signs)) == 1:
        stability = min(100, stability + 18)
    
    # Score de oportunidad: magnitud 7d * estabilidad
    base_magnitude = abs(avg_7d) if avg_7d is not None else 0
    score = round(base_magnitude * (stability / 100), 2)
    
    return stability, score

def main():
    markets = get_markets()
    results = []

    for m in markets:
        try:
            rates = get_funding_rates(m["marketId"])
            avg_7d = average_annualized(rates, 168)
            avg_3d = average_annualized(rates, 72)
            avg_24h = average_annualized(rates, 24)

            # Funding actual (preferir el más reciente del historial)
            current_annualized = None
            if rates:
                try:
                    latest_rate = float(rates[0]["rate"])
                    current_annualized = round(latest_rate * 8760 * 100, 2)
                except (KeyError, ValueError, TypeError):
                    pass

            # Fallback al lastFundingRate del market si no hay historial
            if current_annualized is None:
                last_rate_str = m.get("perpetualMarketFunding", {}).get("lastFundingRate")
                if last_rate_str:
                    try:
                        current_annualized = round(float(last_rate_str) * 8760 * 100, 2)
                    except (ValueError, TypeError):
                        pass

            if avg_7d is not None:
                ticker_upper = m["ticker"].upper()
                base = ticker_upper.split("/")[0].split(" ")[0]

                rwa_keywords = {
                    "SNOW", "DELL", "META", "PANW", "COIN", "ASML", "INTC", "HOOD", "ARM", "LLY",
                    "US500", "SPX", "TSM", "NVDA", "AMGN", "VRT", "GILD", "AMD", "FLUT",
                    "SCHW", "PM", "ANET", "PFE", "QCOM", "GOOGL", "GOOG", "V", "AMC", "MS", "GME", "DIS",
                    "SPOT", "MRVL", "SMCI", "AAPL", "TSLA", "MSFT", "AMZN", "NFLX", "MSTR",
                    "CRCL", "PLTR", "BABA", "NIO", "RIVN", "SOFI", "RBLX", "SNAP", "UBER",
                    "ABNB", "SHOP", "SQ", "PYPL", "JPM", "BAC", "GS", "BLK", "BRK",
                    "NKE", "SBUX", "MCD", "KO", "PEP", "WMT", "TGT", "COST", "HD", "LOW",
                    "BA", "LMT", "RTX", "GD", "NOC", "MRNA", "JNJ", "UNH", "CVS", "C",
                    "USDJPY", "EURUSD", "GBPUSD", "AUDUSD", "USDCAD", "XAU", "XAG", "GOLD",
                    "SILVER", "WTI", "BRENT", "OIL", "CRUDE", "NDX", "DJI",
                    "SPCX", "OPENAI", "ANTHROPIC", "SPACEX", "TTI", "AIX", "TRADFI"
                }

                is_rwa = base in rwa_keywords

                stability, score = calculate_stability_and_score(
                    avg_7d, avg_3d, avg_24h, current_annualized
                )

                results.append({
                    "ticker": m["ticker"],
                    "marketId": m["marketId"],
                    "type": "RWA" if is_rwa else "CRYPTO",
                    "avg_7d_annualized_%": avg_7d,
                    "avg_3d_annualized_%": avg_3d,
                    "avg_24h_annualized_%": avg_24h,
                    "current_funding_annualized_%": current_annualized,
                    "stability": stability,
                    "score": score
                })

        except Exception as e:
            print(f"Error en {m.get('ticker', 'unknown')}: {e}")

        time.sleep(0.12)

    # Ordenar por score de oportunidad (mejor funding estable primero)
    results.sort(key=lambda x: x["score"], reverse=True)

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
