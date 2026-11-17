import streamlit as st
import pandas as pd
import plotly.express as px

from utils.data_loader import load_data, add_derived_columns

st.set_page_config(page_title="Loan Application Analysis", page_icon="💳", layout="wide")

df = add_derived_columns(load_data())

st.title("Loan Application Analysis")
st.caption("Analyze loan amounts, contract types, and key ratios for Home Credit applications")

# Filters
with st.sidebar:
    st.header("Filters")
    contract_options = ["All"] + sorted(df["NAME_CONTRACT_TYPE"].dropna().unique().tolist())
    gender_options = ["All"] + sorted(df["CODE_GENDER"].dropna().unique().tolist())

    contract_filter = st.selectbox("Contract Type", contract_options)
    gender_filter = st.selectbox("Gender", gender_options)

    income_options = ["All", "< 75K", "75K–150K", "150K–300K", "300K–600K", "≥ 600K"]
    credit_options = ["All", "< 250K", "250K–500K", "500K–1M", "1M–2M", "≥ 2M"]

    income_filter = st.selectbox("Income Band", income_options)
    credit_filter = st.selectbox("Credit Band", credit_options)

    target_filter = st.selectbox("Target (Default)", ["All", "Non-default", "Default"])

filtered = df.copy()

if contract_filter != "All":
    filtered = filtered[filtered["NAME_CONTRACT_TYPE"] == contract_filter]
if gender_filter != "All":
    filtered = filtered[filtered["CODE_GENDER"] == gender_filter]

if income_filter != "All":
    filtered = filtered[filtered["INCOME_BAND"].astype(str) == income_filter]

credit_bins = [-float("inf"), 250000, 500000, 1000000, 2000000, float("inf")]
credit_labels = ["< 250K", "250K–500K", "500K–1M", "1M–2M", "≥ 2M"]
credit_band = pd.cut(filtered["AMT_CREDIT"], bins=credit_bins, labels=credit_labels)
if credit_filter != "All":
    filtered = filtered[credit_band.astype(str) == credit_filter]

if target_filter == "Non-default":
    filtered = filtered[filtered["TARGET"] == 0]
elif target_filter == "Default":
    filtered = filtered[filtered["TARGET"] == 1]

n = len(filtered)
total_loan = filtered["AMT_CREDIT"].sum()
avg_loan = filtered["AMT_CREDIT"].mean() if n else 0
median_loan = filtered["AMT_CREDIT"].median() if n else 0
avg_lti = (filtered["AMT_CREDIT"] / filtered["AMT_INCOME_TOTAL"].replace(0, pd.NA)).mean() if n else 0
avg_ati = (filtered["AMT_ANNUITY"] / filtered["AMT_INCOME_TOTAL"].replace(0, pd.NA)).mean() if n else 0
cash_share = (filtered["NAME_CONTRACT_TYPE"].eq("Cash loans").mean() * 100) if n else 0
avg_goods = filtered["AMT_GOODS_PRICE"].mean() if n else 0

k = st.columns(7)
k[0].metric("Total Loan Amount", f"{total_loan:,.0f}")
k[1].metric("Average Loan", f"{avg_loan:,.0f}")
k[2].metric("Median Loan", f"{median_loan:,.0f}")
k[3].metric("Avg. Loan-to-Income", f"{avg_lti:.2f}")
k[4].metric("Avg. Annuity-to-Income", f"{avg_ati:.2f}")
k[5].metric("Cash Loan Share", f"{cash_share:.2f}%")
k[6].metric("Avg. Goods Price", f"{avg_goods:,.0f}")

c1, c2 = st.columns(2)

with c1:
    st.subheader("Loan Amount Distribution")
    fig = px.histogram(filtered, x="AMT_CREDIT", nbins=40)
    fig.update_layout(xaxis_title="Loan Amount", yaxis_title="Applications")
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("Credit Amount by Contract Type")
    contract_df = filtered.groupby("NAME_CONTRACT_TYPE", as_index=False)["AMT_CREDIT"].sum()
    fig = px.bar(contract_df, x="NAME_CONTRACT_TYPE", y="AMT_CREDIT", text="AMT_CREDIT")
    fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
    fig.update_layout(xaxis_title="", yaxis_title="Total Credit")
    st.plotly_chart(fig, use_container_width=True)

c3, c4, c5 = st.columns(3)

with c3:
    st.subheader("Loan-to-Income Distribution")
    ratio = (filtered["AMT_CREDIT"] / filtered["AMT_INCOME_TOTAL"].replace(0, pd.NA)).dropna()
    ratio = ratio.clip(upper=10)
    fig = px.histogram(ratio, nbins=40, labels={"value": "Loan-to-Income"})
    fig.update_layout(xaxis_title="Loan / Income", yaxis_title="Applications")
    st.plotly_chart(fig, use_container_width=True)

with c4:
    st.subheader("Annuity-to-Income: Default vs Non-default")
    temp = filtered.copy()
    temp["ANNUITY_TO_INCOME"] = temp["AMT_ANNUITY"] / temp["AMT_INCOME_TOTAL"].replace(0, pd.NA)
    ati_df = temp.groupby("TARGET", as_index=False)["ANNUITY_TO_INCOME"].mean()
    ati_df["Status"] = ati_df["TARGET"].map({0: "Non-default", 1: "Default"})
    fig = px.bar(ati_df, x="Status", y="ANNUITY_TO_INCOME", text="ANNUITY_TO_INCOME")
    fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
    fig.update_layout(xaxis_title="", yaxis_title="Average Annuity / Income")
    st.plotly_chart(fig, use_container_width=True)

with c5:
    st.subheader("Contract Type Share")
    share = filtered["NAME_CONTRACT_TYPE"].value_counts().reset_index()
    share.columns = ["Contract Type", "Applications"]
    fig = px.pie(share, names="Contract Type", values="Applications", hole=0.55)
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Loan Application Details")
cols = ["SK_ID_CURR", "NAME_CONTRACT_TYPE", "AMT_CREDIT", "AMT_INCOME_TOTAL",
        "AMT_ANNUITY", "AMT_GOODS_PRICE", "TARGET"]
show = filtered[cols].head(10).copy()
show["TARGET"] = show["TARGET"].map({0: "Non-default", 1: "Default"})
st.dataframe(show, use_container_width=True, hide_index=True)
