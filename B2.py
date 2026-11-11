"""Create the three required EV charging visualization panels."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# B2.py is in Final/code; the cleaned CSV is in Final.
PROJECT_DIR = Path(__file__).resolve().parent.parent
INPUT_FILE = PROJECT_DIR / "cleaned_energy_sales_data.csv"
FIGURE_DIR = PROJECT_DIR / "figures"


def load_data() -> pd.DataFrame:
    """Read the cleaned EV session file and check required columns."""
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Could not find {INPUT_FILE}. Run B1.py first."
        )

    data = pd.read_csv(INPUT_FILE)

    required_columns = {
        "Start_Hour",
        "Energy_kWh",
        "User_Type",
        "Net_Billable_MYR",
        "Battery_Temp_C",
    }
    missing = required_columns - set(data.columns)

    if missing:
        raise ValueError(
            f"The cleaned file is missing columns: {sorted(missing)}"
        )

    return data


def create_charts(data: pd.DataFrame) -> None:
    """Create and save three visualization panels and a combined figure."""
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", context="notebook")

    # Panel 1: session energy grouped by start hour.
    # This is only a proxy for grid demand because no meter readings exist.
    hourly_energy = (
        data.groupby("Start_Hour")["Energy_kWh"]
        .sum()
        .reindex(range(24), fill_value=0)
    )

    # Illustrative solar profile: rises after 06:00, peaks at noon,
    # and falls to zero by 18:00. This is not measured campus data.
    hours = np.arange(24)
    solar_profile = 30 * np.maximum(
        0,
        np.sin(np.pi * (hours - 6) / 12),
    )

    fig, axes = plt.subplots(1, 3, figsize=(18, 5.5))

    axes[0].plot(
        hours,
        hourly_energy.values,
        marker="o",
        linewidth=2,
        color="#176B87",
        label="Session energy proxy",
    )
    axes[0].plot(
        hours,
        solar_profile,
        linestyle="--",
        linewidth=2,
        color="#E08E0B",
        label="Illustrative solar profile",
    )
    axes[0].set_title("Hourly Demand Proxy and Solar Profile")
    axes[0].set_xlabel("Session start hour")
    axes[0].set_ylabel("Energy (kWh)")
    axes[0].set_xticks(range(0, 24, 2))
    axes[0].legend(frameon=False, fontsize=8)

    # Panel 2: compare the distribution of session costs by user type.
    user_order = ["Student", "Staff", "Visitor"]
    sns.boxplot(
        data=data,
        x="User_Type",
        y="Net_Billable_MYR",
        order=user_order,
        showfliers=False,
        color="#8FC1B5",
        ax=axes[1],
    )
    axes[1].set_title("Charging Cost by User Type")
    axes[1].set_xlabel("User type")
    axes[1].set_ylabel("Net billable amount (MYR)")

    # Panel 3: battery temperature versus delivered energy with a trendline.
    sns.regplot(
        data=data,
        x="Battery_Temp_C",
        y="Energy_kWh",
        scatter_kws={"alpha": 0.35, "s": 25, "color": "#176B87"},
        line_kws={"color": "#D95F02", "linewidth": 2},
        ax=axes[2],
    )
    axes[2].set_title("Battery Temperature and Energy Delivered")
    axes[2].set_xlabel("Battery temperature (°C)")
    axes[2].set_ylabel("Energy delivered (kWh)")

    fig.suptitle(
        "Smart Campus EV Charging Analysis",
        fontsize=16,
        fontweight="bold",
    )
    fig.tight_layout()

    # Save all three panels together.
    combined_path = FIGURE_DIR / "B2_all_panels.png"
    fig.savefig(combined_path, dpi=300, bbox_inches="tight")

    # Save each chart separately as well.
    for index, axis in enumerate(axes, start=1):
        single_fig = axis.get_figure()
        single_fig.savefig(
            FIGURE_DIR / f"B2_panel_{index}.png",
            dpi=300,
            bbox_inches="tight",
        )

    plt.show()
    plt.close(fig)

    print(f"Saved the three-panel figure to: {combined_path}")
    print(f"Individual chart files are in: {FIGURE_DIR}")


def main() -> None:
    """Load the B1 output and generate the B2 figures."""
    try:
        df = load_data()
        create_charts(df)
    except (OSError, pd.errors.ParserError, ValueError) as error:
        print(f"Could not create charts: {error}")
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()