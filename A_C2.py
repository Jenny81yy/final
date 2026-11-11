from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# A_C2.py 在 Final\code，CSV 在 Final 文件夹
project_dir = Path(__file__).resolve().parent.parent
csv_path = project_dir / "cleaned_energy_sales_data.csv"

# 读取数据，创建 df
df = pd.read_csv(csv_path)

# 这些列确实存在于提供的清理后数据中
available_columns = [
    "Battery_Temp_C",
    "Duration_Mins",
    "Energy_kWh",
]

corr = df[available_columns].corr()

plt.figure(figsize=(7, 5))
sns.heatmap(
    corr,
    annot=True,
    fmt=".2f",
    cmap="vlag",
    center=0,
    vmin=-1,
    vmax=1,
    square=True,
)

plt.title("Correlation Between Available EV Session Measures")
plt.tight_layout()
plt.show()