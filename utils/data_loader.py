from pathlib import Path
import pandas as pd
import streamlit as st

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "application_train.csv"


@st.cache_data
def load_data():
    return pd.read_csv(DATA_PATH)


def add_derived_columns(df):
    data = df.copy()

    # Age in years: DAYS_BIRTH is stored as negative days in the Home Credit dataset.
    data["AGE_YEARS"] = (-data["DAYS_BIRTH"] / 365.25).round(2)

    # Income bands used by the dashboard.
    data["INCOME_BAND"] = pd.cut(
        data["AMT_INCOME_TOTAL"],
        bins=[-float("inf"), 75000, 150000, 300000, 600000, float("inf")],
        labels=["< 75K", "75K–150K", "150K–300K", "300K–600K", "≥ 600K"],
    )

    data["AGE_GROUP"] = pd.cut(
        data["AGE_YEARS"],
        bins=[0, 25, 30, 35, 40, 45, 50, 55, 60, float("inf")],
        labels=["< 25", "25–29", "30–34", "35–39", "40–44",
                "45–49", "50–54", "55–59", "≥ 60"],
        right=False,
    )

    return data
