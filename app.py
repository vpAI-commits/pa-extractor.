import streamlit as st
from google import genai
from google.genai import types
import json

# --- 1. PREMIUM DARK UI CONFIGURATION ---
# Sets wide layout and expands the sidebar for the new control flow
st.set_page_config(page_title="PA Nexus Dashboard", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

# Initialize Session State so results don't disappear when interacting with the page
if "extracted_data" not in st.session_state:
    st.session_state.extracted_data = None

# Injecting Custom CSS for a Dark "Glassmorphism" Enterprise Look
st.markdown("""
    <style>
    /* Dark Theme Background */
    .stApp {
        background-color: #0b0f19;
        background-image: radial-gradient(circle at top left, #1e1e2f, #0b0f19);
        color: #e2e8f0;
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide Streamlit branding to look like a standalone app */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Gradient Text for Main Headers */
    .gradient-text {
        background: linear-gradient(90deg, #00C9FF 0%, #92FE9D 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 0px;
        padding-bottom: 10px;
    }
    .sub-text {
        color: #94a3b8;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    
    /* Glassmorphism Card Styling for Metrics */
    div[data-testid="metric-container"] {
        background: rgba(30, 41, 59, 0.6);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 24px;
        border-left: 4px solid #00C9FF;
        box-shadow: 0 10px 30px -10px rgba(0,0,0,0.5);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 35px -10px rgba(0, 201, 255, 0.3);
    }
    div[data-testid="stMetricLabel"] {
        color: #94a3b8;
        font-weight: 600;
        font-size: 0.95rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    div[data-testid="stMetricValue"] {
        color: #ffffff;
        font-weight: 800;
        font-size: 2.2rem;
    }
    
    /* Neon Gradient Button */
    div.stButton > button:first-child {
        background: linear-gradient(90deg, #00C9FF 0%, #92FE9D 100%);
        color: #0b0f19;
        border-radius: 8px;
        border: none;
        padding: 0.75rem 1.5rem;
        font-weight: 800;
        letter-spacing: 0.5px;
        transition: all 0.3s ease;
    }
    div.stButton > button:first-child:hover {
        transform: scale(1.02);
        box-shadow: 0 0 20px rgba(0, 201, 255, 0.4);
        color: #0b0f19;
    }
    
    /* Alert Box Styling (Info/Warning/Success) */
    div[data-testid="stAlert"] {
        background: rgba(30, 41, 59, 0.6);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        color: #f1f5f9;
    }
    
    /* Empty State Box */
    .empty-state {
        background: rgba(255,255,255,0.02);
        border: 2px dashed rgba(255,255,255,0.1);
        border-radius: 16px;
        padding: 50px;
        text-align: center;
        margin-top: 50px;
    }
    </style>
""", unsafe_allow_html=True)


# --- 2. SIDEBAR: UPLOAD & CONTROLS ---
with st.sidebar:
    st.markdown('<h1 style="color: #00C9FF; margin-bottom: 0;">⚡ PA Nexus</h1>', unsafe_allow_html=True)
    st.markdown("<p style='color: #94a3b8; font-size: 0.9rem;'>AI-Powered Triage Engine</p>", unsafe_allow_html=True)
    st.write("---")
    
    st.markdown("### 📂 Document Ingestion")
    uploaded_file = st.file_uploader("Upload Medical Record", type=["pdf"], label_visibility="collapsed")
    
    if uploaded_file:
        st.success(f"File loaded: **{uploaded_file.name}**")
        st.write("")
        
        if st.button("🚀 Initialize Extraction", use_container_width=True):
            with st.spinner("Processing via Gemini 2.5 Flash..."):
                try:
                    # Read the PDF
                    pdf_bytes = uploaded_file.read()
                    
                    # Connect to Gemini securely
                    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
                    
                    # Instruction prompt
                    prompt = """
                    You are an expert clinical data extractor. Read this medical record.
                    Extract the data and return it strictly as a raw JSON object. Do not include markdown.
                    
                    Schema:
                    {
                      "patient_status": "Brief 2-3 word health status (e.g. 'Stable', 'Critical', 'Routine')",
                      "primary_diagnosis": "Full condition name",
                      "icd_10_code": "Standard alphanumeric billing code (e.g., E11.9)",
                      "requested_drug": "Medication requested (or 'None Found')",
                      "missing_info": "List any missing lab results needed for approval, or output 'Complete'"
                    }
                    """
                    
                    # Send to the Gemini model
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=[
                            types.Part.from_bytes(data=pdf_bytes, mime_type='application/pdf'),
                            prompt
                        ]
                    )
                    
                    # Save results to session state
                    st.session_state.extracted_data = json.loads(response.text)
                    
                except Exception as e:
                    st.error(f"❌ Extraction failed. Error: {e}")
                    st.session_state.extracted_data = None


# --- 3. MAIN AREA: DASHBOARD ---
st.markdown('<p class="gradient-text">Intelligence Dashboard</p>', unsafe_allow_html=True)

# If no data has been extracted yet, show the empty state
if st.session_state.extracted_data is None:
    st.markdown("""
        <div class="empty-state">
            <h2 style="color: #64748b; font-weight: 500;">Awaiting Data Ingestion</h2>
            <p style="color: #475569;">Please upload a clinical document in the sidebar to populate the dashboard.</p>
        </div>
    """, unsafe_allow_html=True)

# If data exists, render the dashboard
else:
    data = st.session_state.extracted_data
    
    st.markdown('<p class="sub-text">Real-time clinical metadata extracted from document</p>', unsafe_allow_html=True)
    
    # Row 1: Key Metrics Cards
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Primary ICD-10", value=data.get("icd_10_code", "N/A"))
    with col2:
        st.metric(label="Requested Rx", value=data.get("requested_drug", "N/A"))
    with col3:
        st.metric(label="Clinical Status", value=data.get("patient_status", "N/A"))
    
    st.write("---")
    
    # Row 2: Deep Dive Information
    st.markdown("### 📋 Clinical Breakdown")
    st.write("")
    
    # Render styled alert boxes for the clinical summary
    st.info(f"**🩺 Primary Diagnosis:** {data.get('primary_diagnosis', 'N/A')}", icon="🩺")
    
    missing_val = data.get('missing_info', 'None')
    if missing_val.lower() in ['none', 'complete', 'n/a']:
        st.success(f"**✅ Action Items:** Document appears complete. ({missing_val})", icon="✅")
    else:
        st.warning(f"**⚠️ Missing Information (Action Required):** {missing_val}", icon="⚠️")
        
    st.write("")
    
    # Raw Code Expander (Premium hidden view for developers)
    with st.expander("⚙️ View Developer Payload (Raw JSON)"):
        st.json(data)
