import streamlit as st
import pandas as pd
import plotly.express as px

from utils.data_loader import load_data, add_derived_columns

st.set_page_config(page_title="Default Risk Analysis", page_icon="⚠️", layout="wide")

df = add_derived_columns(load_data())

st.title("Default Risk Analysis")
st.caption("Analyze default patterns and identify high-risk customer segments")

with st.sidebar:
    st.header("Filters")
    contract_options = ["All"] + sorted(df["NAME_CONTRACT_TYPE"].dropna().unique().tolist())
    gender_options = ["All"] + sorted(df["CODE_GENDER"].dropna().unique().tolist())
    education_options = ["All"] + sorted(df["NAME_EDUCATION_TYPE"].dropna().unique().tolist())
    income_options = ["All"] + ["< 75K", "75K–150K", "150K–300K", "300K–600K", "≥ 600K"]
    age_options = ["All"] + df["AGE_GROUP"].dropna().astype(str).unique().tolist()

    contract_filter = st.selectbox("Contract Type", contract_options)
    gender_filter = st.selectbox("Gender", gender_options)
    education_filter = st.selectbox("Education", education_options)
    income_filter = st.selectbox("Income Band", income_options)
    age_filter = st.selectbox("Age Group", age_options)

filtered = df.copy()
if contract_filter != "All":
    filtered = filtered[filtered["NAME_CONTRACT_TYPE"] == contract_filter]
if gender_filter != "All":
    filtered = filtered[filtered["CODE_GENDER"] == gender_filter]
if education_filter != "All":
    filtered = filtered[filtered["NAME_EDUCATION_TYPE"] == education_filter]
if income_filter != "All":
    filtered = filtered[filtered["INCOME_BAND"].astype(str) == income_filter]
if age_filter != "All":
    filtered = filtered[filtered["AGE_GROUP"].astype(str) == age_filter]

n = len(filtered)
defaults = int(filtered["TARGET"].sum())
nondefaults = n - defaults
rate = defaults / n * 100 if n else 0
avg_credit_defaults = filtered.loc[filtered["TARGET"] == 1, "AMT_CREDIT"].mean() if defaults else 0
avg_income_defaults = filtered.loc[filtered["TARGET"] == 1, "AMT_INCOME_TOTAL"].mean() if defaults else 0

# This is intentionally a segment-level analysis. The application_train.csv file has TARGET,
# but it does not contain a trained PD/probability column.
def segment_rate(frame, column):
    return (
        frame.groupby(column, dropna=False)["TARGET"]
        .mean().mul(100).reset_index(name="Default Rate")
        .sort_values("Default Rate", ascending=False)
    )

# Identify segments whose observed historical default rate is >= 20%.
# This is NOT an individual PD prediction.
high_risk_gender = segment_rate(filtered, "CODE_GENDER")
high_risk_edu = segment_rate(filtered, "NAME_EDUCATION_TYPE")
high_risk_income = segment_rate(filtered, "INCOME_BAND")
high_risk_age = segment_rate(filtered, "AGE_GROUP")
high_risk_contract = segment_rate(filtered, "NAME_CONTRACT_TYPE")

all_segments = pd.concat([
    high_risk_gender.assign(Segment_Type="Gender", Segment=high_risk_gender["CODE_GENDER"].astype(str)),
    high_risk_edu.assign(Segment_Type="Education", Segment=high_risk_edu["NAME_EDUCATION_TYPE"].astype(str)),
    high_risk_income.assign(Segment_Type="Income", Segment=high_risk_income["INCOME_BAND"].astype(str)),
    high_risk_age.assign(Segment_Type="Age", Segment=high_risk_age["AGE_GROUP"].astype(str)),
    high_risk_contract.assign(Segment_Type="Contract", Segment=high_risk_contract["NAME_CONTRACT_TYPE"].astype(str)),
])
high_risk_count = int((all_segments["Default Rate"] >= 20).sum())

k = st.columns(6)
k[0].metric("Total Defaults", f"{defaults:,}")
k[1].metric("Default Rate", f"{rate:.2f}%")
k[2].metric("Non-default Customers", f"{nondefaults:,}")
k[3].metric("High-risk Segments (≥20%)", f"{high_risk_count:,}")
k[4].metric("Avg. Credit (Defaults)", f"{avg_credit_defaults:,.0f}")
k[5].metric("Avg. Income (Defaults)", f"{avg_income_defaults:,.0f}")

c1, c2, c3 = st.columns(3)

with c1:
    st.subheader("Default vs Non-default")
    pie = pd.DataFrame({"Status": ["Default", "Non-default"], "Count": [defaults, nondefaults]})
    fig = px.pie(pie, names="Status", values="Count", hole=0.58)
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("Default Rate by Gender")
    fig = px.bar(high_risk_gender, x="CODE_GENDER", y="Default Rate", text="Default Rate")
    fig.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
    fig.update_layout(xaxis_title="Gender", yaxis_title="Default Rate (%)")
    st.plotly_chart(fig, use_container_width=True)

with c3:
    st.subheader("Default Rate by Education")
    fig = px.bar(high_risk_edu, x="Default Rate", y="NAME_EDUCATION_TYPE",
                 orientation="h", text="Default Rate")
    fig.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
    fig.update_layout(xaxis_title="Default Rate (%)", yaxis_title="Education")
    st.plotly_chart(fig, use_container_width=True)

c4, c5, c6 = st.columns(3)

with c4:
    st.subheader("Default Rate by Income Band")
    fig = px.bar(high_risk_income, x="INCOME_BAND", y="Default Rate", text="Default Rate")
    fig.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
    fig.update_layout(xaxis_title="Income Band", yaxis_title="Default Rate (%)")
    st.plotly_chart(fig, use_container_width=True)

with c5:
    st.subheader("Default Rate by Age Group")
    age_plot = high_risk_age.copy()
    age_plot["AGE_GROUP"] = age_plot["AGE_GROUP"].astype(str)
    fig = px.bar(age_plot, x="AGE_GROUP", y="Default Rate", text="Default Rate")
    fig.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
    fig.update_layout(xaxis_title="Age Group", yaxis_title="Default Rate (%)")
    st.plotly_chart(fig, use_container_width=True)

with c6:
    st.subheader("Default Rate by Contract Type")
    fig = px.bar(high_risk_contract, x="NAME_CONTRACT_TYPE", y="Default Rate", text="Default Rate")
    fig.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
    fig.update_layout(xaxis_title="", yaxis_title="Default Rate (%)")
    st.plotly_chart(fig, use_container_width=True)

st.subheader("High-Risk Customer Segments")
risk_table = all_segments[all_segments["Default Rate"] >= 20][
    ["Segment_Type", "Segment", "Default Rate"]
].sort_values("Default Rate", ascending=False)

if risk_table.empty:
    st.info("No segment in the current filter has an observed historical default rate of 20% or higher.")
else:
    risk_table["Default Rate"] = risk_table["Default Rate"].round(2)
    st.dataframe(risk_table, use_container_width=True, hide_index=True)

st.caption("Note: ≥20% is an observed segment-level default-rate threshold, not a machine-learning PD prediction.")
