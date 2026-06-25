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
                num_col_name = df.columns[pair["num"]] # Follow-ups
                den_col_name = df.columns[pair["den"]] # Evals
                
                # Updated math label for the UI
                if st.sidebar.checkbox(f"{pair['label']} : (F/Us + Evals) / Evals", value=True):
                    selected_pairs.append(pair)

            if not selected_pairs:
                st.warning("Please select at least one ratio from the sidebar to calculate the total.")
            else:
                # --- Calculations ---
                results = []
                total_evals = 0
                total_fus = 0
                
                for pair in selected_pairs:
                    n_idx = pair["num"] # F/Us
                    d_idx = pair["den"] # Evals
                    
                    # Sum the F/Us and Evals for the selected provider
                    f_sum = pd.to_numeric(provider_df.iloc[:, n_idx], errors='coerce').fillna(0).sum()
                    e_sum = pd.to_numeric(provider_df.iloc[:, d_idx], errors='coerce').fillna(0).sum()
                    
                    # Corrected Math: (Follow-ups + Evals) / Evals
                    ratio = (f_sum + e_sum) / e_sum if e_sum != 0 else 0
                    
                    results.append({
                        "Pairing": pair["label"],
                        "F/Us": f_sum,
                        "Evals": e_sum,
                        "Ratio": ratio
                    })
                    
                    # Add to the grand totals
                    total_fus += f_sum
                    total_evals += e_sum
                    
                # Calculate the Grand Total Ratio using the new formula
                grand_total_ratio = (total_fus + total_evals) / total_evals if total_evals != 0 else 0
                
                results_df = pd.DataFrame(results)

                # --- Visualizations ---
                st.subheader(f"📈 Ratio Breakdown for {selected_provider}")
                
                # Top level summary metrics
                m1, m2, m3 = st.columns(3)
                m1.metric("Selected F/Us", f"{total_fus:g}")
                m2.metric("Selected Evals", f"{total_evals:g}")
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

                st.plotly_chart(fig, use_
