import numpy as np
import pandas as pd

# Rows represent hours; columns represent three charging hubs.
grid_load_kw = np.array([
    [120, 135, 160],
    [110, 145, 180],
    [125, 150, 175]
])

# NumPy operation 1: select hours where at least one hub exceeds 170 kW.
peak_hours = grid_load_kw[grid_load_kw.max(axis=1) > 170]

# NumPy operation 2: boolean masking to find temperatures above 45°C.
battery_temp_c = np.array([39.2, 46.1, 43.7, 48.3])
overheated_temps = battery_temp_c[battery_temp_c > 45]

# Example session data for Pandas operations.
sessions = pd.DataFrame({
    "charger_type": ["AC", "DC", "AC", "DC"],
    "power_kw": [7.2, np.nan, 6.8, 28.0],
    "revenue_myr": [12.5, 30.0, 15.0, 42.0]
})

# Pandas operation 1: replace missing power values with the column median.
sessions["power_kw"] = sessions["power_kw"].fillna(
    sessions["power_kw"].median()
)

# Pandas operation 2: calculate total revenue for each charger type.
revenue_by_charger = sessions.groupby("charger_type")["revenue_myr"].sum()

print("Peak-hour load rows:\n", peak_hours)
print("Temperatures above 45°C:", overheated_temps)
print("Sessions after median imputation:\n", sessions)
print("Revenue by charger type:\n", revenue_by_charger)