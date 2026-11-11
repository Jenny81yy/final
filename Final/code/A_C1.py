from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

# A_C1.py 位于 Final\code，CSV 位于 Final
project_dir = Path(__file__).resolve().parent.parent
csv_path = project_dir / "cleaned_energy_sales_data.csv"

print("正在读取：", csv_path)
df = pd.read_csv(csv_path)

# 按开始小时和充电器类型汇总净收入
hourly_revenue = df.pivot_table(
    index="Start_Hour",
    columns="Charger_Type",
    values="Net_Billable_MYR",
    aggfunc="sum",
    fill_value=0,
)

# 确保横轴显示 0 到 23 时
hourly_revenue = hourly_revenue.reindex(range(24), fill_value=0)

# 绘制分组柱状图
ax = hourly_revenue.plot(
    kind="bar",
    figsize=(12, 6),
    width=0.8,
    color=["#2A788E", "#F0A202"],
)

ax.set_title("Hourly Charging Revenue by Charger Type")
ax.set_xlabel("Start Hour")
ax.set_ylabel("Revenue (MYR)")
ax.legend(title="Charger Type", frameon=False)
ax.grid(axis="y", linestyle="--", alpha=0.35)

plt.tight_layout()
plt.show()