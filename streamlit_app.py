import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Provider VPE Ratio", layout="wide")

st.title("📊 Provider VPE Ratio Dashboard")
st.markdown("Upload one or more CSV files to visualize and compare provider-specific ratios across clinics.")

# --- Inputs ---
# UPGRADE: accept_multiple_files=True allows 1 or more files to be uploaded simultaneously
uploaded_files = st.file_uploader("Upload CSV file(s)", type=['csv'], accept_multiple_files=True)

# --- Main App Logic ---
if uploaded_files:
    try:
        st.markdown("---")
        # UPGRADE: A toggle to handle providers who work at multiple clinics
        split_clinics = st.checkbox("Separate providers by clinic (e.g., 'John Doe (QA)' vs 'John Doe (SLU)')", 
                                    value=False, 
                                    help="Check this to compare a provider's performance between clinics. Leave unchecked to merge their totals into one.")
        
        df_list = []
        valid_files = 0
        
        for file in uploaded_files:
            temp_df = pd.read_csv(file)
            
            if "Provider" not in temp_df.columns:
                st.error(f"Error: Could not find a 'Provider' column in '{file.name}'. Skipping this file.")
                continue
            
            # Extract a clean clinic name (e.g., "v5 VPE QA") from the filename
            clinic_name = file.name.split(' [')[0] if ' [' in file.name else file.name.replace('.csv', '')
            
            if split_clinics:
                # Append the clinic name to the provider's name
                temp_df["Provider"] = temp_df["Provider"].astype(str) + f" ({clinic_name})"
            else:
                temp_df["Provider"] = temp_df["Provider"].astype(str)
            
            df_list.append(temp_df)
            valid_files += 1
            
        if df_list:
            # Combine all valid files into one massive dataframe
            df = pd.concat(df_list, ignore_index=True)
            
            st.success(f"Successfully loaded and merged data from {valid_files} clinic(s)!")
            
            with st.expander("Preview Master Data"):
                st.dataframe(df.head())

            st.markdown("---")
            
            # --- Provider Selection ---
            provider_col = "Provider"
            
            # Get unique providers, removing empty rows
            providers = df[provider_col].dropna().astype(str).unique()
            
            # Use multiselect to allow picking multiple providers for comparison
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
                    num_col_name = str(df.columns[pair["num"]]) # F/Us column name
                    den_col_name = str(df.columns[pair["den"]]) # Evals column name
                    
                    label_title = f"{num_col_name} & {den_col_name}"
                    
                    if st.sidebar.checkbox(label_title, value=True):
                        pair["label"] = label_title
                        selected_pairs.append(pair)

                if not selected_pairs:
                    st.warning("Please select at least one ratio from the sidebar to calculate the total.")
                else:
                    # --- Calculations ---
                    all_results = []
                    provider_totals = {}
                    
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
                    
                    cols = st.columns(len(selected_providers))
                    for i, provider in enumerate(selected_providers):
                        with cols[i]:
                            st.markdown(f"**{provider}**")
                            st.metric("Selected F/Us", f"{provider_totals[provider]['Total F/Us']:g}")
                            st.metric("Selected Evals", f"{provider_totals[provider]['Total Evals']:g}")
                            st.metric("Total Aggregated Ratio", f"{provider_totals[provider]['Grand Total Ratio']:.2f}")
                    
                    st.markdown("---")
                    
                    # Grouped Bar Chart
                    fig = px.bar(results_df, x="Pairing", y="Ratio", color="Provider", barmode="group", text="Ratio",
                                 title="Provider Comparison: Individual Pairings")
                    
                    fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
                    
                    color_sequence = px.colors.qualitative.Plotly
                    for i, provider in enumerate(selected_providers):
                        prov_color = color_sequence[i % len(color_sequence)]
                        g_ratio = provider_totals[provider]["Grand Total Ratio"]
                        
                        fig.add_hline(y=g_ratio, line_dash="dash", line_color=prov_color, line_width=2,
                                      annotation_text=f"{provider} Total: {g_ratio:.2f}", 
                                      annotation_position="top right", annotation_font_size=12, annotation_font_color=prov_color)
                    
                    if not results_df.empty and results_df['Ratio'].max() > 0:
                        fig.update_layout(yaxis_range=[0, results_df['Ratio'].max() * 1.3])

                    st.plotly_chart(fig, use_container_width=True)

                    # Data Table View
                    st.subheader("🔢 Computed Data")
                    st.dataframe(results_df, use_container_width=True)
                    
    except Exception as e:
        st.error(f"An error occurred while processing the file: {e}")
