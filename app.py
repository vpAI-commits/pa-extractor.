import streamlit as st
from google import genai
from google.genai import types
import json

# --- 1. PREMIUM DARK UI CONFIGURATION ---
st.set_page_config(page_title="PA Nexus Dashboard", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

if "extracted_data" not in st.session_state:
    st.session_state.extracted_data = None

# Custom CSS for the Dashboard
st.markdown("""
    <style>
    .stApp { background-color: #0b0f19; background-image: radial-gradient(circle at top left, #1e1e2f, #0b0f19); color: #e2e8f0; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .gradient-text { background: linear-gradient(90deg, #00C9FF 0%, #92FE9D 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3rem; font-weight: 800; }
    div[data-testid="metric-container"] { background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 16px; padding: 20px; border-left: 4px solid #00C9FF; }
    div[data-testid="stMetricValue"] { color: #ffffff; font-weight: 800; font-size: 2rem; }
    .decision-box { background: rgba(15, 23, 42, 0.8); border: 2px solid #3b82f6; border-radius: 16px; padding: 30px; text-align: center; margin-bottom: 20px;}
    .approved { border-color: #22c55e; box-shadow: 0 0 20px rgba(34, 197, 94, 0.2); }
    .denied { border-color: #ef4444; box-shadow: 0 0 20px rgba(239, 68, 68, 0.2); }
    .pending { border-color: #f59e0b; box-shadow: 0 0 20px rgba(245, 158, 11, 0.2); }
    </style>
""", unsafe_allow_html=True)

# --- 2. SIDEBAR: DUAL UPLOAD ZONES ---
with st.sidebar:
    st.markdown('<h1 style="color: #00C9FF;">⚡ PA Nexus</h1>', unsafe_allow_html=True)
    st.markdown("<p style='color: #94a3b8; font-size: 0.9rem;'>Dual-Document Adjudication</p>", unsafe_allow_html=True)
    st.write("---")
    
    st.markdown("### 📄 1. Patient Record")
    patient_file = st.file_uploader("Upload Patient Medical PDF", type=["pdf"], label_visibility="collapsed")
    
    st.write("")
    
    st.markdown("### 🏛️ 2. PBM Policy")
    policy_file = st.file_uploader("Upload Formulary Rules PDF", type=["pdf"], label_visibility="collapsed")
    
    st.write("---")
    
    # Only show the button if BOTH files are uploaded
    if patient_file and policy_file:
        if st.button("🚀 Run Full Adjudication", use_container_width=True):
            with st.spinner("Analyzing rules & comparing patient data..."):
                try:
                    # Read both PDFs into memory
                    patient_bytes = patient_file.read()
                    policy_bytes = policy_file.read()
                    
                    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
                    
                    # Package both PDFs for the AI
                    patient_pdf_part = types.Part.from_bytes(data=patient_bytes, mime_type='application/pdf')
                    policy_pdf_part = types.Part.from_bytes(data=policy_bytes, mime_type='application/pdf')
                    
                    # The Adjudication Prompt
                    prompt = """
                    You are a strict PBM Clinical Pharmacist Adjudicator.
                    You have been provided with TWO PDF documents:
                    1. A Patient Medical Record
                    2. A PBM Formulary Policy Document
                    
                    TASK: Read the patient's record, identify the requested drug, find the exact rules for that drug in the Policy Document, and make an adjudication decision.
                    
                    RULES FOR DECISION:
                    1. If patient meets ALL policy criteria, decision is "APPROVED".
                    2. If patient explicitly fails a criterion, decision is "DENIED".
                    3. If policy requires specific information missing from the Patient PDF, decision is "PENDING_INFO".
                    
                    Output strictly as JSON:
                    {
                      "patient_status": "Brief health status",
                      "primary_diagnosis": "Full condition name",
                      "icd_10_code": "Billing code",
                      "requested_drug": "Medication requested",
                      "missing_info": "List missing data or 'None'",
                      "decision": "APPROVED", "DENIED", or "PENDING_INFO",
                      "reasoning": "Explain why based strictly on comparing the PDF facts to the PDF rules.",
                      "message_to_provider": "Draft request to doctor if PENDING_INFO, else 'N/A'"
                    }
                    """
                    
                    # Send BOTH documents and the prompt to Gemini
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=[patient_pdf_part, policy_pdf_part, prompt]
                    )
                    
                    st.session_state.extracted_data = json.loads(response.text)
                    
                except Exception as e:
                    st.error(f"Error processing documents: {e}")

# --- 3. MAIN DASHBOARD ---
st.markdown('<p class="gradient-text">Adjudication Dashboard</p>', unsafe_allow_html=True)

if st.session_state.extracted_data:
    data = st.session_state.extracted_data
    
    # Showcase the final decision front and center
    decision = data.get("decision", "UNKNOWN")
    box_class = "approved" if decision == "APPROVED" else "denied" if decision == "DENIED" else "pending"
    color = "#22c55e" if decision == "APPROVED" else "#ef4444" if decision == "DENIED" else "#f59e0b"
    
    st.markdown(f"""
        <div class="decision-box {box_class}">
            <h3 style="color: #94a3b8; margin: 0; text-transform: uppercase; letter-spacing: 2px;">AI System Decision</h3>
            <h1 style="color: {color}; font-size: 3.5rem; margin: 10px 0;">{decision}</h1>
            <p style="color: #e2e8f0; font-size: 1.1rem; margin: 0;">{data.get('reasoning', '')}</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Key Metrics
    col1, col2, col3 = st.columns(3)
    with col1: st.metric(label="Primary ICD-10", value=data.get("icd_10_code", "N/A"))
    with col2: st.metric(label="Requested Rx", value=data.get("requested_drug", "N/A"))
    with col3: st.metric(label="Clinical Status", value=data.get("patient_status", "N/A"))
    
    st.write("---")
    
    # Show Provider Fax if Pending Info
    if decision == "PENDING_INFO":
        st.warning(f"**📠 Auto-Drafted Fax to Provider:**\n\n{data.get('message_to_provider', 'N/A')}", icon="✉️")
    
    with st.expander("⚙️ View Developer Payload"):
        st.json(data)
else:
    st.info("Awaiting Documents... Please upload both the Medical Record and the PBM Policy in the sidebar to begin.")
