# Home Credit Risk Analytics - Streamlit

## Pages implemented
1. Executive Overview
2. Customer Demographics
3. Loan Application Analysis
4. Default Risk Analysis
5. Income & Employment
6. Credit Bureau Analysis

## Important
Pages 1–5 work with `application_train.csv`.

Page 6 is wired for the official `bureau.csv` dataset used by the reference dashboard.
If `bureau.csv` is not present, the page explains what file is needed instead of failing.

## Project structure
home_credit_streamlit/
├── app.py
├── requirements.txt
├── data/
│   └── application_train.csv
├── utils/
│   └── data_loader.py
└── pages/
    ├── 1_Executive_Overview.py
    ├── 2_Customer_Demographics.py
    ├── 3_Loan_Application_Analysis.py
    ├── 4_Default_Risk_Analysis.py
    ├── 5_Income_Employment.py
    └── 6_Credit_Bureau_Analysis.py

## Run
pip install -r requirements.txt
streamlit run app.py

## Libraries
- Python
- Streamlit
- Pandas
- Plotly

