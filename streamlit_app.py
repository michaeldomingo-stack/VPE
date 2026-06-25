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
    provider_df = df[df[provider_col].astype(str) == selected_provider]

    # Map the Excel column letters to pandas integer indexes
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

    max_col_index = df.shape[1] - 1
    valid_pairs = [p for p in ratio_pairs if p["num"] <= max_col_index and p["den"] <= max_col_index]

    st.sidebar.header("Toggle Ratios")
    st.sidebar.write("Select which metrics to include for the selected provider:")
    
    selected_pairs = []
    for pair in valid_pairs:
        num_col_name = df.columns[pair["num"]]
        den_col_name = df.columns[pair["den"]]
        
        if st.sidebar.checkbox(f"{pair['label']} : Evals ({num_col_name}) / F/Us ({den_col_name})", value=True):
            selected_pairs.append(pair)

    if not selected_pairs:
        st.warning("Please select at least one ratio from the sidebar to calculate the total.")
    else:
        # --- Calculations ---
        results = []
        total_evals = 0
        total_fus = 0
        
        for pair in selected_pairs:
            n_idx = pair["num"]
            d_idx = pair["den"]
            
            # Sum the Evals (num) and F/Us (den) for the selected provider
            n_sum = pd.to_numeric(provider_df.iloc[:, n_idx], errors='coerce').fillna(0).sum()
            d_sum = pd.to_numeric(provider_df.iloc[:, d_idx], errors='coerce').fillna(0).sum()
            
            # Calculate the individual pairing ratio
            ratio = n_sum / d_sum if d_sum != 0 else 0
            
            results.append({
                "Pairing": pair["label"],
                "Total Evals": n_sum,
                "Total F/Us": d_sum,
                "Ratio": ratio
            })
            
            # Add to the grand totals
            total_evals += n_sum
            total_fus += d_sum
            
        # Calculate the Grand Total Ratio (Sum of selected Evals / Sum of selected F/Us)
        grand_total_ratio = total_evals / total_fus if total_fus != 0 else 0
        
        results_df = pd.DataFrame(results)

        # --- Visualizations ---
        st.subheader(f"📈 Ratio Breakdown for {selected_provider}")
        
        # Top level summary metrics
        m1, m2, m3 = st.columns(3)
        m1.metric("Selected Evals", f"{total_evals:g}")
        m2.metric("Selected F/Us", f"{total_fus:g}")
        m3.metric("Total Aggregated Ratio", f"{grand_total_ratio:.2f}")
        
        # Create Bar Chart
        fig = px.bar(results_df, x="Pairing", y="Ratio", text="Ratio",
                     title=f"Individual Pairings vs. Total Ratio ({selected_provider})",
                     color_discrete_sequence=['#4A90E2'])
        
        # Format the numbers on top of the bars
        fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        
        # Add a horizontal dashed line representing the Total Ratio
        fig.add_hline(y=grand_total_ratio, line_dash="dash", line_color="red", line_width=3,
                      annotation_text=f"Total Ratio: {grand_total_ratio:.2f}", 
                      annotation_position="top right", annotation_font_size=14, annotation_font_color="red")
        
        # Tweak the chart layout to give the labels room to breathe
        if not results_df.empty and results_df['Ratio'].max() > 0:
            fig.update_layout(yaxis_range=[0, results_df['Ratio'].max() * 1.2])

        st.plotly_chart(fig, use_container_width=True)

        # Data Table View
        st.subheader("🔢 Computed Data")
        st.dataframe(results_df, use_container_width=True)
