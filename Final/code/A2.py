from functools import reduce

# Real-world simulation of campus charging session records:
# (Session_ID, Charger_Type, Duration_Mins, Overstay_Mins, Battery_Temp_C, Base_Fee_MYR)
charging_sessions = [
    ("SESS-101", "AC", 120, 25, 42.5, 15.0),  # Overstay 25>20, Temp 42.5>40 -> High risk
    ("SESS-102", "DC", 45, 5, 38.0, 30.0),   # Normal
    ("SESS-103", "DC", 90, 35, 46.1, 50.0),   # Overstay 35>20, Temp 46.1>40 -> High risk
    ("SESS-104", "AC", 60, 0, 31.0, 10.0),   # Normal
    ("SESS-105", "DC", 110, 40, 41.8, 40.0)   # Overstay 40>20, Temp 41.8>40 -> High risk
]

# 1. Filter: Extract high-risk sessions where overstay time exceeds 20 minutes AND battery temperature exceeds 40°C
high_risk_sessions = list(filter(
    lambda s: s[3] > 20 and s[4] > 40.0,
    charging_sessions
))

# 2. Map: Calculate a 15% surcharge penalty for the identified high-risk sessions
surcharged_sessions = list(map(
    lambda s: {
        "Session_ID": s[0],
        "Base_Fee": s[5],
        "Surcharge": s[5] * 0.15  # 15% surcharge applied to the base fee
    },
    high_risk_sessions
))

# 3. Reduce: Calculate the total surcharge revenue generated across all alert sessions
total_surcharge_revenue = reduce(
    lambda acc, curr: acc + curr["Surcharge"],
    surcharged_sessions,
    0.0  # Initial accumulator value set to 0.0
)

# Print execution results
print(f"Total High-Risk Alert Sessions: {len(high_risk_sessions)}")
for item in surcharged_sessions:
    print(f" - Session {item['Session_ID']}: Base Fee MYR {item['Base_Fee']:.2f} -> Surcharge MYR {item['Surcharge']:.2f}")
print(f"Total Surcharge Revenue Generated: MYR {total_surcharge_revenue:.2f}")