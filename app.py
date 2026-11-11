#Smart Campus EV charging dashboard.

from pathlib import Path
from datetime import date

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st


# app.py is in Final/code; CSV files are in Final.
PROJECT_DIR = Path(__file__).resolve().parent.parent
SESSION_FILE = PROJECT_DIR / "cleaned_energy_sales_data.csv"
SALES_FILE = PROJECT_DIR / "sales_data.csv"

st.set_page_config(
    page_title="Smart Campus EV Dashboard",
    page_icon="⚡",
    layout="wide",
)


@st.cache_data
def load_sessions(file_path: str, modified_time: float) -> pd.DataFrame:
    """Read the cleaned charging session data."""
    del modified_time  # Used to refresh Streamlit's cache when the file changes.
    return pd.read_csv(file_path)


@st.cache_data
def load_sales(file_path: str, modified_time: float) -> pd.DataFrame:
    """Read the sales transaction data."""
    del modified_time
    return pd.read_csv(file_path)


def apply_filters(
    data: pd.DataFrame,
    minimum_energy: float,
    selected_chargers: list[str],
    date_range: tuple[date, date],
) -> pd.DataFrame:
    """Apply filters that are supported by the session data."""
    filtered = data.loc[data["Energy_kWh"] >= minimum_energy].copy()

    if selected_chargers:
        filtered = filtered.loc[
            filtered["Charger_Type"].isin(selected_chargers)
        ].copy()

    # The supplied EV session data does not contain a session date.
    # Apply this filter only if a Session_Date field is later added.
    if "Session_Date" in filtered.columns:
        session_dates = pd.to_datetime(
            filtered["Session_Date"],
            errors="coerce",
        ).dt.date
        filtered = filtered.loc[
            session_dates.between(date_range[0], date_range[1])
        ].copy()

    return filtered


def show_overview(
    filtered: pd.DataFrame,
    all_sessions: pd.DataFrame,
    temperature_limit: float,
) -> None:
    """Display KPIs, revenue chart, and high-risk alerts."""
    energy_total = filtered["Energy_kWh"].sum()
    carbon_total = filtered["Carbon_Savings_kgCO2"].sum()
    revenue_total = filtered["Net_Billable_MYR"].sum()

    alerts = filtered.loc[
        (filtered["Overstay_Mins"] > 20)
        & (filtered["Battery_Temp_C"] > temperature_limit)
    ]

    all_alerts = all_sessions.loc[
        (all_sessions["Overstay_Mins"] > 20)
        & (all_sessions["Battery_Temp_C"] > temperature_limit)
    ]

    # The deltas compare the selected filters with all sessions.
    # They are not period-to-period changes because no session dates exist.
    cols = st.columns(4)
    cols[0].metric(
        "Total Energy Delivered",
        f"{energy_total:,.1f} kWh",
        delta=f"{energy_total - all_sessions['Energy_kWh'].sum():+,.1f} kWh",
    )
    cols[1].metric(
        "Carbon Offset",
        f"{carbon_total:,.1f} kg CO₂",
        delta=(
            f"{carbon_total - all_sessions['Carbon_Savings_kgCO2'].sum():+,.1f} kg"
        ),
    )
    cols[2].metric(
        "Total Session Revenue",
        f"MYR {revenue_total:,.2f}",
        delta=(
            f"{revenue_total - all_sessions['Net_Billable_MYR'].sum():+,.2f} MYR"
        ),
    )
    cols[3].metric(
        "Active Alert Count",
        f"{len(alerts):,}",
        delta=f"{len(alerts) - len(all_alerts):+d} vs all sessions",
        delta_color="inverse",
    )

    st.caption(
        "KPI deltas compare the current filtered records with all session records."
    )

    if alerts.empty:
        st.success("No high-risk sessions meet the current alert conditions.")
    else:
        st.error(
            f"{len(alerts)} high-risk session(s) need review: "
            "overstay exceeds 20 minutes and battery temperature exceeds "
            f"{temperature_limit:.1f}°C."
        )
        st.dataframe(alerts, use_container_width=True, hide_index=True)

    st.subheader("Hourly Charging Revenue by Charger Type")
    revenue_by_hour = filtered.pivot_table(
        index="Start_Hour",
        columns="Charger_Type",
        values="Net_Billable_MYR",
        aggfunc="sum",
        fill_value=0,
    ).reindex(range(24), fill_value=0)

    st.bar_chart(revenue_by_hour)


def show_explorer(filtered: pd.DataFrame) -> None:
    """Display session temperature-energy and cost charts."""
    st.header("Session Explorer")

    if filtered.empty:
        st.info("No sessions match the selected filters.")
        return

    left, right = st.columns(2)

    with left:
        st.subheader("Charging Cost by User Type")
        fig, ax = plt.subplots(figsize=(7, 4))
        sns.boxplot(
            data=filtered,
            x="User_Type",
            y="Net_Billable_MYR",
            showfliers=False,
            ax=ax,
        )
        ax.set_xlabel("User type")
        ax.set_ylabel("Net billable amount (MYR)")
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    with right:
        st.subheader("Battery Temperature and Energy")
        fig, ax = plt.subplots(figsize=(7, 4))
        sns.regplot(
            data=filtered,
            x="Battery_Temp_C",
            y="Energy_kWh",
            scatter_kws={"alpha": 0.35, "s": 22},
            line_kws={"color": "#D95F02"},
            ax=ax,
        )
        ax.set_xlabel("Battery temperature (°C)")
        ax.set_ylabel("Energy delivered (kWh)")
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    st.caption(
        "The session file has no ambient temperature or measured grid-load "
        "column. Battery temperature and session energy are the available "
        "measures shown here."
    )


def show_sales_page() -> None:
    """Display sales transactions separately from EV charging sessions."""
    st.header("Sales Transactions")

    if not SALES_FILE.exists():
        st.warning(f"Sales data file not found: {SALES_FILE}")
        return

    sales = load_sales(
        str(SALES_FILE),
        SALES_FILE.stat().st_mtime,
    )

    sales["Transaction_Date"] = pd.to_datetime(
        sales["Transaction_Date"],
        errors="coerce",
    )

    valid_dates = sales["Transaction_Date"].dropna()

    if not valid_dates.empty:
        selected_dates = st.date_input(
            "Transaction date range",
            value=(
                valid_dates.min().date(),
                valid_dates.max().date(),
            ),
            key="sales_date_range",
        )

        if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
            start_date, end_date = selected_dates
            sales = sales.loc[
                sales["Transaction_Date"].dt.date.between(
                    start_date,
                    end_date,
                )
            ].copy()

    total_sales = sales["Total_Revenue_MYR"].sum()
    st.metric("Filtered Sales Revenue", f"MYR {total_sales:,.2f}")
    st.dataframe(sales, use_container_width=True, hide_index=True)


def main() -> None:
    """Run the interactive dashboard."""
    st.sidebar.title("Campus EV Analytics")

    page = st.sidebar.radio(
        "Dashboard page",
        ["Executive Overview", "Session Explorer", "Sales Transactions"],
    )

    try:
        if not SESSION_FILE.exists():
            raise FileNotFoundError(
                f"Cleaned session data was not found: {SESSION_FILE}. "
                "Run B1.py first."
            )

        sessions = load_sessions(
            str(SESSION_FILE),
            SESSION_FILE.stat().st_mtime,
        )

        st.sidebar.header("Session Filters")

        minimum_energy = st.sidebar.slider(
            "Minimum energy (kWh)",
            min_value=0.0,
            max_value=float(sessions["Energy_kWh"].max()),
            value=0.0,
            step=0.5,
        )

        charger_options = sorted(
            sessions["Charger_Type"].dropna().unique().tolist()
        )
        selected_chargers = st.sidebar.multiselect(
            "Charger type",
            options=charger_options,
            default=charger_options,
        )

        selected_dates = st.sidebar.date_input(
            "Session date range",
            value=(date.today(), date.today()),
            key="session_date_range",
        )

        if not isinstance(selected_dates, tuple) or len(selected_dates) != 2:
            selected_dates = (selected_dates, selected_dates)

        temperature_limit = st.sidebar.slider(
            "High-risk temperature threshold (°C)",
            min_value=30.0,
            max_value=60.0,
            value=40.0,
            step=0.5,
        )

        filtered = apply_filters(
            sessions,
            minimum_energy,
            selected_chargers,
            selected_dates,
        )

        if "Session_Date" not in sessions.columns:
            st.sidebar.info(
                "The supplied session file has no date column, so the "
                "session date filter is currently inactive."
            )

        if page == "Executive Overview":
            st.title("Smart Campus Energy and EV Fleet")
            show_overview(filtered, sessions, temperature_limit)
        elif page == "Session Explorer":
            show_explorer(filtered)
        else:
            show_sales_page()

        st.subheader("Filtered Session Data")
        st.dataframe(filtered, use_container_width=True, hide_index=True)

        st.download_button(
            label="Download filtered sessions as CSV",
            data=filtered.to_csv(index=False).encode("utf-8"),
            file_name="filtered_energy_sessions.csv",
            mime="text/csv",
        )

    except (
        OSError,
        KeyError,
        ValueError,
        pd.errors.ParserError,
    ) as error:
        st.error(f"Could not load the dashboard data: {error}")


if __name__ == "__main__":
    main()