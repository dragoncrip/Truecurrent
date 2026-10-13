# Clasificación CRYPTO / RWA basada en los mercados reales de TrueCurrent
ticker_upper = m["ticker"].upper()

rwa_keywords = [
    # Acciones / Equities (extraídas de la interfaz)
    "SNOW", "DELL", "META", "PANW", "COIN", "ASML", "INTC", "HOOD", "ARM", "LLY",
    "US500", "SPX", "TSM", "NVDA", "AMGN", "VRT", "GOLD", "XAU", "AMD", "FLUT",
    "SCHW", "PM", "ANET", "PFE", "QCOM", "GOOGL", "V", "AMC", "EM", "GME", "DIS",
    "SPOT", "MRVL", "SMCI", "AAPL", "TSLA", "MSFT", "AMZN", "NFLX", "MSTR",
    "CRCL", "PLTR", "BABA", "NIO", "RIVN", "SOFI", "RBLX", "SNAP", "UBER",
    "ABNB", "SHOP", "SQ", "PYPL", "JPM", "BAC", "GS", "MS", "BLK", "BRK",
    "NKE", "SBUX", "MCD", "KO", "PEP", "WMT", "TGT", "COST", "HD", "LOW",
    "BA", "LMT", "RTX", "GD", "NOC", "PFE", "MRNA", "JNJ", "UNH", "CVS",
    # Macro / Commodities / FX
    "USDJPY", "EURUSD", "GBPUSD", "XAU", "XAG", "WTI", "BRENT", "GOLD", "SILVER",
    "OIL", "CRUDE", "US500", "SPX", "NDX", "DJI",
    # Pre-IPO / Especiales
    "SPCX", "OPENAI", "ANTHROPIC", "SPACEX", "TTI", "AIX", "TRADFI"
]

is_rwa = any(keyword in ticker_upper for keyword in rwa_keywords)

results.append({
    "ticker": m["ticker"],
    "marketId": m["marketId"],
    "type": "RWA" if is_rwa else "CRYPTO",
    "avg_7d_annualized_%": avg_7d,
    "current_funding_annualized_%": current_annualized,
    "price_change_24h_%": price_change_24h
})
