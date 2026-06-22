import streamlit as st
from google import genai
from google.genai import types
import json

# --- 1. PREMIUM UI CONFIGURATION ---
# Sets wide layout and hides the sidebar for a cleaner app feel
st.set_page_config(page_title="PA AI Triage", page_icon="✨", layout="wide", initial_sidebar_state="collapsed")

# Injecting Custom CSS for a Premium Enterprise Look
st.markdown("""
    <style>
    /* Main background and font */
    .stApp {
        background-color: #f8fafc;
        font-family: 'Inter', sans-serif;
    }
    /* Hide Streamlit branding to look like a standalone app */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Premium Header */
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 0px;
        padding-bottom: 0px;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #64748b;
        margin-bottom: 2rem;
    }
    
    /* Card Styling for Metrics (Adds white background and drop shadows) */
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        transition: transform 0.2s ease-in-out;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -2px rgba(0, 0, 0, 0.04);
    }
    div[data-testid="metric-container"] label {
        color: #64748b;
        font-weight: 600;
        font-size: 0.95rem;
    }
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
        color: #0f172a;
        font-weight: 800;
        font-size: 2rem;
    }
    
    /* Premium Gradient Button */
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        letter-spacing: 0.5px;
        box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.3);
        transition: all 0.3s ease;
    }
    div.stButton > button:first-child:hover {
        background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%);
        box-shadow: 0 6px 8px -1px rgba(37, 99, 235, 0.4);
        transform: translateY(-1px);
        color: white;
    }
    
    /* File uploader styling */
    .stFileUploader > div > div {
        background-color: #ffffff;
        border: 2px dashed #cbd5e1;
        border-radius: 12px;
        padding: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.markdown('<p class="main-header">✨ AI Prior Auth Engine</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Enterprise clinical extraction and triaging powered by Google Gemini.</p>', unsafe_allow_html=True)

# --- 2. FILE UPLOADER UI ---
st.markdown("### 📂 1. Upload Clinical Document")
uploaded_file = st.file_uploader("Drop Patient Medical Record (PDF)", type=["pdf"], label_visibility="collapsed")

if uploaded_file:
    st.success(f"📄 **{uploaded_file.name}** securely loaded into memory.")
    st.write("") # spacing
    
    # Create a nice wide button
    if st.button("🚀 Analyze & Extract Data", use_container_width=True):
        
        # Show a loading spinner while the AI thinks
        with st.spinner("🧠 Gemini 2.5 Flash is analyzing document structure and extracting clinical entities..."):
            try:
                # Read the PDF
                pdf_bytes = uploaded_file.read()
                
                # Connect to Gemini securely
                client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
                
                # The precise instruction for the AI
                prompt = """
                You are an expert clinical data extractor. Read this medical record.
                Extract the data and return it strictly as a raw JSON object. Do not include markdown.
                
                Schema:
                {
                  "patient_status": "Brief 2-3 word health status (e.g. 'Stable', 'Critical', 'Routine Checkup')",
                  "primary_diagnosis": "Full condition name",
                  "icd_10_code": "Standard alphanumeric billing code (e.g., E11.9)",
                  "requested_drug": "Medication requested (or 'None Found')",
                  "missing_info": "List any missing lab results needed for approval, or output 'Complete'"
                }
                """
                
                # Send to the Gemini model (LOCKED TO FLASH FOR HIGH SPEED/NO RATE LIMITS)
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=[
                        types.Part.from_bytes(data=pdf_bytes, mime_type='application/pdf'),
                        prompt
                    ]
                )
                
                # Turn the text into readable data
                data = json.loads(response.text)
                
                # --- 3. PREMIUM DASHBOARD UI ---
                st.write("---")
                st.markdown("### 📊 2. Extraction Dashboard")
                st.write("")
                
                # Row 1: Key Metrics Cards (Styled by our custom CSS)
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(label="Primary ICD-10", value=data.get("icd_10_code", "N/A"))
                with col2:
                    st.metric(label="Requested Rx", value=data.get("requested_drug", "N/A"))
                with col3:
                    st.metric(label="Clinical Status", value=data.get("patient_status", "N/A"))
                
                st.write("")
                st.write("")
                
                # Row 2: Deep Dive Information
                st.markdown("#### 📋 Clinical Summary")
                
                # Use a premium container for the summary
                with st.container():
                    st.info(f"**🩺 Primary Diagnosis:** {data.get('primary_diagnosis', 'N/A')}")
                    
                    missing_val = data.get('missing_info', 'None')
                    if missing_val.lower() in ['none', 'complete', 'n/a']:
                        st.success(f"**✅ Action Items:** Document appears complete. ({missing_val})")
                    else:
                        st.warning(f"**⚠️ Missing Information (Action Required):** {missing_val}")
                    
                st.write("")
                
                # Raw Code Expander (Premium hidden view for developers)
                with st.expander("⚙️ View Developer Payload (Raw JSON)"):
                    st.json(data)
                    
            except Exception as e:
                st.error(f"❌ An error occurred during extraction. Please ensure the PDF is readable. Error details: {e}")
