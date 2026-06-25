import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import re

st.set_page_config(page_title="Provider VPE Ratio", layout="wide")

st.title("📊 Provider VPE Ratio Dashboard")
st.markdown("Upload your Excel sheet or paste your Google Sheets link to visualize provider-specific ratios.")

# --- Helper Functions ---
def parse_google_sheet_url(url):
    """Converts a Google Sheets URL into a direct CSV export URL for pandas."""
    match = re.search(r'/d/([a-zA-Z0-9-_]+)', url)
    gid_match = re.search(r'gid=([0-9]+)', url)
    
    if match:
        file_id = match.group(1)
        gid = gid_match.group(1) if gid_match else '0'
        return f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=csv&gid={gid}"
    return None

@st.cache_data
def load_data(file_or_url, is_url=False):
    """Loads data from file upload or Google Sheets URL"""
    try:
        if is_url:
            csv_url = parse_google_sheet_url(file_or_url)
            if not csv_url:
                st.error("Invalid Google Sheets URL.")
                return None
            df = pd.read_csv(csv_url)
        else:
            xls = pd.ExcelFile(file_or_url)
            if "VPE Calculations" in xls.sheet_names:
                df = pd.read_excel(file_or_url, sheet_name="VPE Calculations")
            else:
                df = pd.read_excel(file_or_url) 
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

# --- Inputs ---
input_method = st.radio("Choose Input Method:", ("Google Sheets Link", "File Upload"))

df = None

if input_method == "Google Sheets Link":
    gs_url = st.text_input("Paste Google Sheets URL here:", placeholder="https://docs.google.com/spreadsheets/d/...")
    if gs_url:
        df = load_data(gs_url, is_url=True)
else:
    uploaded_file = st.file_uploader("Upload Excel/CSV", type=['xlsx', 'csv'])
    if uploaded_file:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = load_data(uploaded_file, is_url=False)

# --- Main App Logic ---
if df is not None:
    st.success("Data loaded successfully!")
    
    with st.expander("Preview Raw Data"):
        st.dataframe(df.head())

    st.markdown("---")
    
    # --- Provider Selection ---
    col1, col2 = st.columns(2)
    with col1:
        # Dynamically ask which column holds the provider names (defaults to the first column)
        provider_col = st.selectbox("1. Which column contains the Provider names?", df.columns.tolist(), index=0)
    
    with col2:
        # Get unique providers, removing empty rows, and create a dropdown
        providers = df[provider_col].dropna().astype(str).unique()
        selected_provider = st.selectbox("2. Select a Provider to analyze:", sorted(providers))
    
    # Filter the dataframe to ONLY show rows for the selected provider
    provider
