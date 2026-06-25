import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Provider VPE Ratio", layout="wide")

st.title("📊 Provider VPE Ratio Dashboard")
st.markdown("Upload your CSV file to visualize provider-specific ratios.")

# --- Inputs ---
uploaded_file = st.file_uploader("Upload CSV file", type=['csv'])

# --- Main App Logic ---
if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        st.success("Data loaded successfully!")
        
        with st.expander("Preview Raw Data"):
            st.dataframe(df.head())

        st.markdown("---")
        
        # --- Provider Selection ---
        # Hardcode the column name to exactly "Provider"
        provider_col = "Provider"
        
        if provider_col not in df.columns:
            st.error(f"Error: Could not find a column named '{provider_col}' in your CSV. Please check your column headers.")
        else:
            # Get unique providers, removing empty rows, and create a dropdown
            providers = df[provider_col].dropna().astype(str).unique()
            selected_provider = st.selectbox("Select a Provider to analyze:", sorted(providers))
        
            # Filter the dataframe to ONLY show rows for the selected provider
            provider_df = df[df[provider_col].astype(str) == selected_provider]

            # Map the Excel column letters to pandas integer indexes
            ratio_pairs = [
                {"label": "Ratio 1 (C/B)", "num": 2, "den": 1},
                {"label": "Ratio 2 (F/E)", "num": 5, "den": 4},
                {"label": "Ratio 3 (I/H)", "num": 8, "den": 7},
                {"label": "Ratio 4 (L/K)", "num": 11, "den": 10},
                {"label": "Ratio 5 (O/N)", "num": 14, "den": 13},
                {"label": "Ratio 6 (R
