#Clean EV charging sessions and export engineered energy metrics.

from pathlib import Path

import numpy as np
import pandas as pd


# B1.py is in Final/code; the CSV files are in the parent Final directory.
PROJECT_DIR = Path(__file__).resolve().parent.parent
INPUT_FILE = PROJECT_DIR / "ev_campus_dataset (1).csv"
OUTPUT_FILE = PROJECT_DIR / "cleaned_energy_sales_data.csv"

NUMERIC_COLUMNS = [
    "Start_Hour",
    "Duration_Mins",
    "Energy_kWh",
    "Overstay_Mins",
    "Battery_Temp_C",
]

CATEGORY_RULES = {
    "Charger_Type": {"AC", "DC"},
    "User_Type": {"Student", "Staff", "Visitor"},
    "Grid_Status_Label": {"Normal", "Grid_Surge", "Overheated"},
}

# These are explicit example tariff assumptions because the raw CSV
# does not provide the campus's official pricing rules.
HOURLY_RATE_MYR = {
    "AC": 6.00,
    "DC": 15.00,
}
PEAK_SURCHARGE_RATE = 0.25
PEAK_HOURS = {12, 13, 14}
OVERSTAY_FREE_MINUTES = 20
OVERSTAY_RATE_MYR_PER_MIN = 0.20
CARBON_FACTOR_KG_PER_KWH = 0.475


def clean_sessions(data: pd.DataFrame) -> pd.DataFrame:
    """Validate, impute, and engineer metrics for EV charging sessions."""
    required_columns = {
        "Session_ID",
        *NUMERIC_COLUMNS,
        *CATEGORY_RULES.keys(),
    }
    missing_columns = required_columns - set(data.columns)

    if missing_columns:
        raise ValueError(
            f"Input CSV is missing required columns: "
            f"{sorted(missing_columns)}"
        )

    # Work on a copy so the original DataFrame remains unchanged.
    cleaned = data.copy()

    # Convert numeric values; invalid strings become missing values.
    for column in NUMERIC_COLUMNS:
        cleaned[column] = pd.to_numeric(
            cleaned[column],
            errors="coerce",
        )

    # Median imputation is applied separately to each numeric column.
    for column in NUMERIC_COLUMNS:
        median_value = cleaned[column].median()

        if pd.isna(median_value):
            raise ValueError(
                f"Cannot impute {column}: the entire column is missing."
            )

        cleaned[column] = cleaned[column].fillna(median_value)

    # Validate categories and replace invalid labels with the most common
    # valid value in that column.
    for column, allowed_values in CATEGORY_RULES.items():
        cleaned[column] = cleaned[column].astype("string").str.strip()
        valid_mask = cleaned[column].isin(allowed_values)
        invalid_count = int((~valid_mask).sum())

        if invalid_count:
            valid_values = cleaned.loc[valid_mask, column]
            mode_values = valid_values.mode()

            if mode_values.empty:
                raise ValueError(
                    f"No valid category values remain in {column}."
                )

            cleaned.loc[~valid_mask, column] = mode_values.iloc[0]
            print(
                f"Replaced {invalid_count} invalid value(s) "
                f"in {column}."
            )

    # Avoid negative physical values caused by invalid input.
    cleaned["Duration_Mins"] = cleaned["Duration_Mins"].clip(lower=0)
    cleaned["Energy_kWh"] = cleaned["Energy_kWh"].clip(lower=0)
    cleaned["Overstay_Mins"] = cleaned["Overstay_Mins"].clip(lower=0)

    # Feature engineering.
    cleaned["Duration_Hours"] = cleaned["Duration_Mins"] / 60

    # Use NumPy divide to avoid division-by-zero errors.
    cleaned["Power_Rate_kW"] = np.divide(
        cleaned["Energy_kWh"],
        cleaned["Duration_Hours"],
        out=np.zeros(len(cleaned), dtype=float),
        where=cleaned["Duration_Hours"].to_numpy() > 0,
    )

    cleaned["Carbon_Savings_kgCO2"] = (
        cleaned["Energy_kWh"] * CARBON_FACTOR_KG_PER_KWH
    )

    # Apply hourly rates according to charger type.
    cleaned["Base_Rate_MYR"] = cleaned["Charger_Type"].map(
        HOURLY_RATE_MYR
    )
    cleaned["Base_Fee_MYR"] = (
        cleaned["Duration_Hours"] * cleaned["Base_Rate_MYR"]
    )

    # Apply the peak surcharge once if the session starts during a peak
    # hour or the source marks the grid as being in surge status.
    is_peak = (
        cleaned["Start_Hour"].isin(PEAK_HOURS)
        | cleaned["Grid_Status_Label"].eq("Grid_Surge")
    )
    cleaned["Peak_Surge_MYR"] = (
        cleaned["Base_Fee_MYR"]
        * PEAK_SURCHARGE_RATE
        * is_peak.astype(float)
    )

    # Charge only for overstay minutes beyond the 20-minute allowance.
    billable_overstay_mins = (
        cleaned["Overstay_Mins"] - OVERSTAY_FREE_MINUTES
    ).clip(lower=0)

    cleaned["Overstay_Fee_MYR"] = (
        billable_overstay_mins * OVERSTAY_RATE_MYR_PER_MIN
    )

    cleaned["Net_Billable_MYR"] = (
        cleaned["Base_Fee_MYR"]
        + cleaned["Peak_Surge_MYR"]
        + cleaned["Overstay_Fee_MYR"]
    )

    return cleaned


def main() -> None:
    """Read the source CSV, export cleaned data, and print summaries."""
    try:
        if not INPUT_FILE.exists():
            raise FileNotFoundError(
                f"Could not find input file: {INPUT_FILE}"
            )

        raw_data = pd.read_csv(INPUT_FILE)

        print(f"Input file: {INPUT_FILE}")
        print(f"Rows loaded: {len(raw_data):,}")
        print("\nMissing values before cleaning:")
        print(raw_data.isna().sum().to_string())

        cleaned_data = clean_sessions(raw_data)
        cleaned_data.to_csv(OUTPUT_FILE, index=False)

        print(f"\nCleaned data saved to: {OUTPUT_FILE}")
        print("\nNumeric summary statistics:")
        print(
            cleaned_data.select_dtypes(include="number")
            .describe()
            .round(2)
            .to_string()
        )

        print("\nRevenue by charger type (MYR):")
        print(
            cleaned_data.groupby("Charger_Type")["Net_Billable_MYR"]
            .sum()
            .round(2)
            .to_string()
        )

    except (OSError, pd.errors.ParserError, ValueError) as error:
        print(f"Data pipeline failed: {error}")
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()