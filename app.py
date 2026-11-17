import streamlit as st

st.set_page_config(
    page_title="Home Credit Risk Analytics",
    page_icon="🏦",
    layout="wide",
)

st.title("🏦 Home Credit Risk Analytics")
st.subheader("Loan default risk analysis dashboard")
st.write(
    "Use the pages from the sidebar to explore applications, "
    "customer demographics, and default-risk patterns."
)

st.info(
    "This project is built with Python + Streamlit + Pandas + Plotly. "
    "The first two dashboard pages are implemented; more pages will be added step by step."
)
