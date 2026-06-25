import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import re

st.set_page_config(page_title="VPE Ratio Calculator", layout="wide")

st.title("📊 VPE Ratio Dashboard")
st.markdown("Upload your Excel sheet or paste your Google Sheets link to visualize your ratios.")

# --- Helper Functions ---
def parse_google_sheet_url(url):
    """Converts a Google Sheets URL into a direct CSV export URL for pandas."""
    # Extract the file ID
    match = re.search(r'/d/([a-zA-Z0-9-_]+)', url)
    # Extract the gid (tab ID)
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
            # If user uploads an excel file, look for the specific tab
            xls = pd.ExcelFile(file_or_url)
            if "VPE Calculations" in xls.sheet_names:
                df = pd.read_excel(file_or_url, sheet_name="VPE Calculations")
            else:
                df = pd.read_excel(file_or_url) # Fallback to first sheet
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

    # Map the Excel column letters to pandas integer indexes (A=0, B=1, C=2, etc.)
    # We define the pairs based on your prompt: C/B, F/E, I/H, L/K, O/N, R/Q, U/T, X/W, AA/Z
    ratio_pairs = [
        {"label": "Ratio 1 (C/B)", "num": 2, "den": 1},
        {"label": "Ratio 2 (F/E)", "num": 5, "den": 4},
        {"label": "Ratio 3 (I/H)", "num": 8, "den": 7},
        {"label": "Ratio 4 (L/K)", "num": 11, "den": 10},
        {"label": "Ratio 5 (O/N)", "num": 14, "den": 13},
        {"label": "Ratio 6 (R/Q)", "num": 17, "den": 16},
        {"label": "Ratio 7 (U/T)", "num": 20, "den": 19},
        {"label": "Ratio 8 (X/W)", "num": 23, "den": 22},
        {"label": "Ratio 9 (AA/Z)", "num": 26, "den": 25},
    ]

    # Filter out pairs if the dataframe doesn't have enough columns
    max_col_index = df.shape[1] - 1
    valid_pairs = [p for p in ratio_pairs if p["num"] <= max_col_index and p["den"] <= max_col_index]

    st.sidebar.header("Toggle Ratios")
    st.sidebar.write("Select which metrics to include in the Total Ratio Calculation:")
    
    selected_pairs = []
    for pair in valid_pairs:
        # Get actual column names to make the UI friendlier
        num_col_name = df.columns[pair["num"]]
        den_col_name = df.columns[pair["den"]]
        
        # Toggle checkbox
        if st.sidebar.checkbox(f"{pair['label']} : {num_col_name} / {den_col_name}", value=True):
            selected_pairs.append(pair)

    if not selected_pairs:
        st.warning("Please select at least one ratio from the sidebar to calculate the total.")
    else:
        # --- Calculations ---
        # Assuming Column A (index 0) is the X-axis (e.g., Date, Week, or ID)
        x_col = df.columns[0] 
        
        # We need to clean data to ensure we are doing math on numbers (ignoring strings/NaNs)
        calc_df = df.copy()
        
        total_num = np.zeros(len(calc_df))
        total_den = np.zeros(len(calc_df))

        # Calculate individual ratios for the chart and aggregate the totals
        for pair in selected_pairs:
            n_idx = pair["num"]
            d_idx = pair["den"]
            
            # Convert to numeric, forcing errors to NaN, then fill NaNs with 0
            n_vals = pd.to_numeric(calc_df.iloc[:, n_idx], errors='coerce').fillna(0)
            d_vals = pd.to_numeric(calc_df.iloc[:, d_idx], errors='coerce').fillna(0)
            
            total_num += n_vals
            total_den += d_vals
            
            # Create individual ratio column (safely handling division by zero)
            calc_df[pair['label']] = np.where(d_vals != 0, n_vals / d_vals, 0)

        # Calculate Total Aggregated Ratio
        calc_df['Total Ratio'] = np.where(total_den != 0, total_num / total_den, 0)

        # --- Visualizations ---
        st.subheader("📈 Ratio Trends Over Time")
        
        # Get list of ratio columns to plot
        cols_to_plot = [p['label'] for p in selected_pairs] + ['Total Ratio']
        
        # Melt the dataframe for Plotly (makes plotting multiple lines much easier)
        melted_df = calc_df.melt(id_vars=[x_col], value_vars=cols_to_plot, 
                                 var_name='Metric', value_name='Ratio')

        # Create Plotly figure
        fig = px.line(melted_df, x=x_col, y='Ratio', color='Metric', markers=True,
                      title="Individual Selected Ratios vs. Total Aggregated Ratio")
        
        # Make the 'Total Ratio' line thicker and dashed to stand out
        for trace in fig.data:
            if trace.name == 'Total Ratio':
                trace.line.width = 4
                trace.line.dash = 'dash'
        
        st.plotly_chart(fig, use_container_width=True)

        # Data Table View
        st.subheader("🔢 Computed Data")
        display_cols = [x_col] + cols_to_plot
        st.dataframe(calc_df[display_cols])