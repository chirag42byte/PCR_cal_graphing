import requests
import time
from datetime import datetime
import matplotlib.pyplot as plt

# For live interactive plotting
plt.ion()

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/option-chain",
    "Connection": "keep-alive",
}

def get_index_data(index="NIFTY"):
    url_home = "https://www.nseindia.com"
    url_api = f"https://www.nseindia.com/api/option-chain-indices?symbol={index}"

    session = requests.Session()
    session.get(url_home, headers=headers)
    response = session.get(url_api, headers=headers)
    response.raise_for_status()

    data = response.json()
    spot_price = data["records"]["underlyingValue"]
    return spot_price, data

def get_strikes(data, spot_price, n=3):
    strikes = sorted(data["records"]["strikePrices"])
    closest = min(strikes, key=lambda x: abs(x - spot_price))
    idx = strikes.index(closest)
    start = max(0, idx - n)
    end = min(len(strikes), idx + n + 1)
    return strikes[start:end]

def calculate_pcr_with_details(data, selected_strikes):
    calls_oi_changes = []
    puts_oi_changes = []

    for strike in selected_strikes:
        ce_change = 0
        pe_change = 0
        for entry in data["records"]["data"]:
            if entry["strikePrice"] == strike:
                if "CE" in entry:
                    ce_change = entry["CE"].get("changeinOpenInterest", 0)
                if "PE" in entry:
                    pe_change = entry["PE"].get("changeinOpenInterest", 0)
                break
        calls_oi_changes.append((strike, ce_change))
        puts_oi_changes.append((strike, pe_change))

    total_calls = sum(change for _, change in calls_oi_changes)
    total_puts = sum(change for _, change in puts_oi_changes)
    total_abs = abs(total_calls) + abs(total_puts)

    call_pct = (abs(total_calls) / total_abs * 100) if total_abs else 0
    put_pct = (abs(total_puts) / total_abs * 100) if total_abs else 0
    pcr = (abs(total_puts) / abs(total_calls)) if total_calls != 0 else float("inf")

    return {
        "calls_oi_changes": calls_oi_changes,
        "puts_oi_changes": puts_oi_changes,
        "total_calls": total_calls,
        "total_puts": total_puts,
        "call_pct": round(call_pct, 2),
        "put_pct": round(put_pct, 2),
        "pcr": round(pcr, 2),
    }

def main(interval=300):
    pcr_history = []
    timestamps = []
    MAX_POINTS = 20  # Limit the number of points shown

    try:
        while True:
            spot_price, data = get_index_data("NIFTY")
            selected_strikes = get_strikes(data, spot_price)
            result = calculate_pcr_with_details(data, selected_strikes)

            current_time = datetime.now().strftime('%H:%M')
            pcr_value = result['pcr']

            timestamps.append(current_time)
            pcr_history.append(pcr_value)

            if len(pcr_history) > MAX_POINTS:
                timestamps.pop(0)
                pcr_history.pop(0)

            # --- Print to Console ---
            print(f"\n[{current_time}] Spot Price: {spot_price}, PCR: {pcr_value}")
            print(f"Selected Strikes: {selected_strikes}")
            print("Call OI Changes:", result['calls_oi_changes'])
            print("Put OI Changes:", result['puts_oi_changes'])

            # --- Plotting ---
            plt.clf()
            plt.plot(timestamps, pcr_history, marker='o', color='blue')
            plt.title("Live NIFTY PCR Trend")
            plt.xlabel("Time")
            plt.ylabel("PCR")
            plt.grid(True)
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.pause(0.1)

            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n⛔ Program stopped by user.")
        plt.ioff()
        plt.show()

if __name__ == "__main__":
    main(interval=300)  # Refresh every 5 minutes
