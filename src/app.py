"""
COREP Reporting Assistant - Streamlit UI
Professional regulatory reporting interface for UK Banks.
"""

import streamlit as st
import pandas as pd
from engine import process_reporting_scenario

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="COREP Reporting Assistant",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# PROFESSIONAL SLATE THEME (Dark/Light Mode Compatible)
# ============================================================================

st.markdown("""
    <style>
    /* Import professional font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Global font override */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Override Streamlit's default colors with Slate palette */
    :root {
        --slate-50: #f8fafc;
        --slate-100: #f1f5f9;
        --slate-200: #e2e8f0;
        --slate-300: #cbd5e1;
        --slate-400: #94a3b8;
        --slate-500: #64748b;
        --slate-600: #475569;
        --slate-700: #334155;
        --slate-800: #1e293b;
        --slate-900: #0f172a;
    }
    
    /* Sidebar header text - override blue color */
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] .stMarkdown h3,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h1 {
        color: var(--slate-700) !important;
    }
    
    /* Sidebar background */
    [data-testid="stSidebar"],
    section[data-testid="stSidebar"] {
        background-color: var(--slate-50) !important;
    }
    
    /* Override any markdown styling in sidebar */
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span {
        color: var(--slate-700) !important;
    }
    
    /* Main content headers */
    h1, h2, h3, h4, h5, h6 {
        color: var(--slate-900) !important;
    }
    
    /* Primary button styling - Slate palette */
    .stButton>button {
        width: 100%;
        border-radius: 6px;
        background-color: var(--slate-600) !important;
        color: white !important;
        border: none;
        font-weight: 600;
        padding: 0.75rem 1.5rem;
        transition: all 0.2s ease;
        letter-spacing: 0.025em;
    }
    .stButton>button:hover {
        background-color: var(--slate-700) !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        transform: translateY(-1px);
    }
    .stButton>button:active {
        background-color: var(--slate-800) !important;
        transform: translateY(0);
    }
    
    /* Text area styling */
    .stTextArea textarea {
        border: 1px solid var(--slate-300) !important;
        border-radius: 6px;
        font-family: 'Inter', monospace;
        transition: border-color 0.2s ease;
        background-color: white !important;
        color: var(--slate-900) !important;
    }
    .stTextArea textarea:focus {
        border-color: var(--slate-600) !important;
        box-shadow: 0 0 0 3px rgba(71, 85, 105, 0.1) !important;
    }
    
    /* Selectbox styling - override blue color */
    .stSelectbox > div > div {
        background-color: white !important;
        border-color: var(--slate-300) !important;
    }
    .stSelectbox label {
        color: var(--slate-700) !important;
    }
    /* Selected option text color */
    .stSelectbox [data-baseweb="select"] > div {
        color: var(--slate-900) !important;
        background-color: white !important;
        border-color: var(--slate-300) !important;
    }
    /* Dropdown options */
    [data-baseweb="popover"] {
        background-color: white !important;
    }
    [role="option"] {
        color: var(--slate-900) !important;
    }
    [role="option"]:hover {
        background-color: var(--slate-100) !important;
    }
    
    /* Metric styling */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
        color: var(--slate-900) !important;
    }
    [data-testid="stMetricLabel"] {
        color: var(--slate-600) !important;
    }
    
    /* Table styling */
    .dataframe {
        border: 1px solid var(--slate-200) !important;
        border-radius: 6px;
        overflow: hidden;
    }
    .dataframe thead tr th {
        background-color: var(--slate-50) !important;
        color: var(--slate-600) !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        font-size: 0.75rem;
        letter-spacing: 0.05em;
        padding: 0.75rem !important;
        border-bottom: 2px solid var(--slate-300) !important;
    }
    .dataframe tbody tr td {
        padding: 0.75rem !important;
        border-bottom: 1px solid var(--slate-100) !important;
        color: var(--slate-800) !important;
    }
    .dataframe tbody tr:hover {
        background-color: var(--slate-50) !important;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: var(--slate-100) !important;
        border-radius: 6px;
        font-weight: 600;
        color: var(--slate-700) !important;
    }
    
    /* Info/warning boxes */
    .stAlert {
        border-radius: 6px;
    }
    
    /* Remove Streamlit branding */
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    
    /* Dark mode adjustments */
    @media (prefers-color-scheme: dark) {
        [data-testid="stSidebar"],
        section[data-testid="stSidebar"] {
            background-color: var(--slate-900) !important;
        }
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] .stMarkdown h3,
        [data-testid="stSidebar"] .stMarkdown h2,
        [data-testid="stSidebar"] .stMarkdown h1,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h1 {
            color: var(--slate-200) !important;
        }
        [data-testid="stSidebar"] .stMarkdown,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span {
            color: var(--slate-300) !important;
        }
        h1, h2, h3, h4, h5, h6 {
            color: var(--slate-100) !important;
        }
        [data-testid="stMetricValue"] {
            color: var(--slate-100) !important;
        }
        [data-testid="stMetricLabel"] {
            color: var(--slate-400) !important;
        }
        .stTextArea textarea {
            background-color: var(--slate-800) !important;
            color: var(--slate-100) !important;
            border-color: var(--slate-600) !important;
        }
        .dataframe thead tr th {
            background-color: var(--slate-800) !important;
            color: var(--slate-300) !important;
        }
        .dataframe tbody tr td {
            color: var(--slate-200) !important;
        }
        .dataframe tbody tr:hover {
            background-color: var(--slate-800) !important;
        }
        .streamlit-expanderHeader {
            background-color: var(--slate-800) !important;
            color: var(--slate-200) !important;
        }
        /* Selectbox in dark mode */
        .stSelectbox > div > div,
        .stSelectbox [data-baseweb="select"] > div {
            background-color: var(--slate-800) !important;
            color: var(--slate-100) !important;
            border-color: var(--slate-600) !important;
        }
        .stSelectbox label {
            color: var(--slate-300) !important;
        }
        [data-baseweb="popover"] {
            background-color: var(--slate-800) !important;
        }
        [role="option"] {
            color: var(--slate-100) !important;
        }
        [role="option"]:hover {
            background-color: var(--slate-700) !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# SIDEBAR - TEMPLATE SELECTION & METADATA
# ============================================================================

with st.sidebar:
    st.title("🏦 COREP Assistant")
    st.divider()
    
    st.markdown("### Template Configuration")
    template = st.selectbox(
        "Active Template",
        ["C 01.00 (Own Funds)"],
        help="Select the COREP template for data extraction"
    )
    
    st.divider()
    
    st.markdown("### System Information")
    st.caption("**Version:** PRA 2026.1.0")
    st.caption("**Model:** Gemini 2.0 Flash")
    st.caption("**Jurisdiction:** UK PRA Rulebook")
    
    st.divider()
    
    st.markdown("### Input Modes")
    st.markdown("""
    **Numeric Input**  
    Enter a single value to auto-map to R010 (CET1 Capital)
    
    **Narrative Input**  
    Describe the scenario in natural language for full extraction
    """)

# ============================================================================
# MAIN INTERFACE - DATA INPUT & RESULTS
# ============================================================================

st.title("COREP Reporting Assistant")
st.markdown("**Regulatory Reporting Automation for UK Banks**")
st.markdown("---")

# Two-column layout for input and results
col1, col2 = st.columns([1, 1], gap="large")

# --- LEFT COLUMN: Data Input ---
with col1:
    st.subheader("📝 Data Input")
    
    user_input = st.text_area(
        "Scenario Description or Numerical Value",
        height=200,
        placeholder="Enter a narrative scenario (e.g., 'The bank has £50m in CET1 capital...') or a single numerical value (e.g., '50000000')",
        help="Supports both narrative descriptions and raw numerical inputs. Numeric values are automatically mapped to Common Equity Tier 1 Capital (R010)."
    )
    
    col_btn1, col_btn2 = st.columns([3, 1])
    
    with col_btn1:
        process_button = st.button("⚡ PROCESS SCENARIO", use_container_width=True)
    
    with col_btn2:
        if st.button("🗑️", help="Clear results"):
            if 'data' in st.session_state:
                del st.session_state['data']
                st.rerun()
    
    if process_button:
        if user_input and user_input.strip():
            with st.spinner("Processing regulatory scenario..."):
                st.session_state['data'] = process_reporting_scenario(user_input)
                st.session_state['input_text'] = user_input
        else:
            st.warning("⚠️ Please provide input data before processing.")

# --- RIGHT COLUMN: Results Display ---
with col2:
    st.subheader("📊 Reporting Extract")
    
    if 'data' in st.session_state:
        data = st.session_state['data']
        
        if "error" in data:
            st.error(f"❌ **Processing Error**\n\n{data['error']}")
        else:
            # Create DataFrame with results
            df = pd.DataFrame(data["results"])
            
            # Format currency values
            df['formatted_value'] = df['value'].apply(lambda x: f"£{x:,.2f}")
            
            # Display table with selected columns
            display_df = df[['row_id', 'field_name', 'formatted_value']].copy()
            display_df.columns = ['Row ID', 'Field Name', 'Amount (GBP)']
            
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )
            
            # Aggregate metrics
            st.markdown("---")
            col_m1, col_m2 = st.columns(2)
            
            with col_m1:
                total_capital = df['value'].sum()
                st.metric(
                    "Aggregate Capital",
                    f"£{total_capital:,.2f}",
                    help="Sum of all extracted capital components"
                )
            
            with col_m2:
                st.metric(
                    "Fields Extracted",
                    len(df),
                    help="Number of COREP fields populated"
                )
    else:
        st.info("ℹ️ Enter scenario data and click **PROCESS SCENARIO** to generate reporting extract.")

# ============================================================================
# EXPANDABLE JUSTIFICATION LOG
# ============================================================================

if 'data' in st.session_state and "results" in st.session_state['data']:
    st.markdown("---")
    
    with st.expander("📋 **Justification & Audit Log**", expanded=False):
        st.markdown("**Regulatory Rule Mappings**")
        st.caption("This log shows the PRA Rulebook references used to justify each field mapping.")
        
        for idx, res in enumerate(st.session_state['data']["results"], 1):
            st.markdown(f"""
            **{idx}. {res['row_id']} - {res['field_name']}**  
            - **Value:** £{res['value']:,.2f}  
            - **Justification:** {res['justification']}
            """)
            
            if idx < len(st.session_state['data']["results"]):
                st.divider()
