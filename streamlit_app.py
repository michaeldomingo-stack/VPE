import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Provider VPE Ratio", layout="wide")

st.title("📊 Provider VPE Ratio Dashboard")
st.markdown("Upload your CSV file to visualize and compare provider-specific ratios.")

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
            # Get unique providers, removing empty rows
            providers = df[provider_col].dropna().astype(str).unique()
            
            # UPGRADE: Use multiselect to allow picking multiple providers for comparison
            selected_providers = st.multiselect("Select Providers to analyze and compare:", sorted(providers), default=[sorted(providers)[0]])
        
            if not selected_providers:
                st.warning("Please select at least one provider.")
            else:
                # Map the Excel column letters to pandas integer indexes
                ratio_pairs = [
                    {"num": 2, "den": 1},
                    {"num": 5, "den": 4},
                    {"num": 8, "den": 7},
                    {"num": 11, "den": 10},
                    {"num": 14, "den": 13},
                    {"num": 17, "den": 16},
                    {"num": 20, "den": 19},
                    {"num": 23, "den": 22},
                    {"num": 26, "den": 25},
                ]

                max_col_index = df.shape[1] - 1
                valid_pairs = [p for p in ratio_pairs if p["num"] <= max_col_index and p["den"] <= max_col_index]

                st.sidebar.header("Toggle Ratios")
                st.sidebar.write("Select which metrics to include:")
                
                selected_pairs = []
                for pair in valid_pairs:
                    # UPGRADE: Pull the exact column names from Row 1
                    num_col_name = str(df.columns[pair["num"]]) # F/Us column name
                    den_col_name = str(df.columns[pair["den"]]) # Evals column name
                    
                    label_title = f"{num_col_name} & {den_col_name}"
                    
                    # Create the toggle using the dynamic title
                    if st.sidebar.checkbox(label_title, value=True):
                        pair["label"] = label_title
                        selected_pairs.append(pair)

                if not selected_pairs:
                    st.warning("Please select at least one ratio from the sidebar to calculate the total.")
                else:
                    # --- Calculations ---
                    all_results = []
                    provider_totals = {}
                    
                    # UPGRADE: Loop through every selected provider to build comparison data
                    for provider in selected_providers:
                        provider_df = df[df[provider_col].astype(str) == provider]
                        
                        total_evals = 0
                        total_fus = 0
                        
                        for pair in selected_pairs:
                            n_idx = pair["num"] # F/Us
                            d_idx = pair["den"] # Evals
                            
                            f_sum = pd.to_numeric(provider_df.iloc[:, n_idx], errors='coerce').fillna(0).sum()
                            e_sum = pd.to_numeric(provider_df.iloc[:, d_idx], errors='coerce').fillna(0).sum()
                            
                            # Math: (Follow-ups + Evals) / Evals
                            ratio = (f_sum + e_sum) / e_sum if e_sum != 0 else 0
                            
                            all_results.append({
                                "Provider": provider,
                                "Pairing": pair["label"],
                                "F/Us": f_sum,
                                "Evals": e_sum,
                                "Ratio": ratio
                            })
                            
                            total_fus += f_sum
                            total_evals += e_sum
                            
                        # Calculate the Grand Total Ratio for this specific provider
                        grand_total_ratio = (total_fus + total_evals) / total_evals if total_evals != 0 else 0
                        
                        # Store totals for the UI metrics
                        provider_totals[provider] = {
                            "Total F/Us": total_fus,
                            "Total Evals": total_evals,
                            "Grand Total Ratio": grand_total_ratio
                        }
                        
                    results_df = pd.DataFrame(all_results)

                    # --- Visualizations ---
                    st.subheader("📈 Ratio Breakdown & Comparison")
                    
                    # UPGRADE: Create dynamic columns to show metrics for each selected provider side-by-side
                    cols = st.columns(len(selected_providers))
                    for i, provider in enumerate(selected_providers):
                        with cols[i]:
                            st.markdown(f"**{provider}**")
                            st.metric("Selected F/Us", f"{provider_totals[provider]['Total F/Us']:g}")
                            st.metric("Selected Evals", f"{provider_totals[provider]['Total Evals']:g}")
                            st.metric("Total Aggregated Ratio", f"{provider_totals[provider]['Grand Total Ratio']:.2f}")
                    
                    st.markdown("---")
                    
                    # UPGRADE: Create Grouped Bar Chart
                    fig = px.bar(results_df, x="Pairing", y="Ratio", color="Provider", barmode="group", text="Ratio",
                                 title="Provider Comparison: Individual Pairings")
                    
                    fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
                    
                    # UPGRADE: Add a color-matched horizontal dashed line for each provider's Grand Total Ratio
                    color_sequence = px.colors.qualitative.Plotly
                    for i, provider in enumerate(selected_providers):
                        prov_color = color_sequence[i % len(color_sequence)]
                        g_ratio = provider_totals[provider]["Grand Total Ratio"]
                        
                        fig.add_hline(y=g_ratio, line_dash="dash", line_color=prov_color, line_width=2,
                                      annotation_text=f"{provider} Total: {g_ratio:.2f}", 
                                      annotation_position="top right", annotation_font_size=12, annotation_font_color=prov_color)
                    
                    # Tweak the chart layout to give the labels room to breathe
                    if not results_df.empty and results_df['Ratio'].max() > 0:
                        fig.update_layout(yaxis_range=[0, results_df['Ratio'].max() * 1.3])

                    st.plotly_chart(fig, use_container_width=True)

                    # Data Table View
                    st.subheader("🔢 Computed Data")
                    st.dataframe(results_df, use_container_width=True)
                    
    except Exception as e:
        st.error(f"An error occurred while processing the file: {e}")
