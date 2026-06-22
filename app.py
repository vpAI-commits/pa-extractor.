import streamlit as st
from google import genai
from google.genai import types
import json

# --- 1. COMPACT UI CONFIGURATION ---
st.set_page_config(page_title="PA Nexus", page_icon="⚕️", layout="wide", initial_sidebar_state="expanded")

if "extracted_data" not in st.session_state:
    st.session_state.extracted_data = None

# Custom CSS for a High-Density, Professional Clinical Look
st.markdown("""
    <style>
    /* Clean, professional background */
    .stApp { background-color: #f8fafc; font-family: 'Inter', -apple-system, sans-serif; color: #1e293b; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    
    /* Tighter general spacing */
    .block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 1200px; }
    h1, h2, h3 { margin-bottom: 0.5rem; }
    
    /* Compact Metric Cards */
    div[data-testid="metric-container"] { 
        background-color: #ffffff; 
        border: 1px solid #e2e8f0; 
        border-radius: 8px; 
        padding: 12px 16px; 
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    div[data-testid="stMetricLabel"] { color: #64748b; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
    div[data-testid="stMetricValue"] { color: #0f172a; font-size: 1.5rem; font-weight: 700; line-height: 1.2; }
    
    /* Compact Decision Banner */
    .decision-banner { 
        border-radius: 8px; 
        padding: 16px 20px; 
        display: flex; 
        align-items: center; 
        gap: 15px; 
        margin-bottom: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .decision-banner h2 { margin: 0; font-size: 1.4rem; font-weight: 700; text-transform: uppercase; }
    .decision-banner p { margin: 0; font-size: 0.95rem; line-height: 1.4; opacity: 0.9; }
    
    .approved { background-color: #ecfdf5; border-left: 6px solid #10b981; color: #065f46; }
    .denied { background-color: #fef2f2; border-left: 6px solid #ef4444; color: #991b1b; }
    .pending { background-color: #fffbeb; border-left: 6px solid #f59e0b; color: #92400e; }
    
    /* Tighter sidebar elements */
    .css-1d391kg { padding-top: 2rem; }
    </style>
""", unsafe_allow_html=True)

# --- 2. SIDEBAR: COMPACT UPLOAD ZONES ---
with st.sidebar:
    st.markdown('<h2 style="color: #0ea5e9; font-weight: 800; margin-top: 0;">⚕️ PA Nexus</h2>', unsafe_allow_html=True)
    st.caption("Clinical Adjudication Engine")
    st.divider()
    
    st.markdown("**1. Patient Record**")
    patient_file = st.file_uploader("Upload Medical PDF", type=["pdf"], label_visibility="collapsed", key="pat")
    
    st.write("")
    
    st.markdown("**2. PBM Policy**")
    policy_file = st.file_uploader("Upload Policy PDF", type=["pdf"], label_visibility="collapsed", key="pol")
    
    st.divider()
    
    if patient_file and policy_file:
        if st.button("Run Adjudication", type="primary", use_container_width=True):
            with st.spinner("Analyzing documents..."):
                try:
                    patient_bytes = patient_file.read()
                    policy_bytes = policy_file.read()
                    
                    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
                    
                    patient_part = types.Part.from_bytes(data=patient_bytes, mime_type='application/pdf')
                    policy_part = types.Part.from_bytes(data=policy_bytes, mime_type='application/pdf')
                    
                    prompt = """
                    You are a strict PBM Clinical Pharmacist Adjudicator.
                    Evaluate the provided Patient Medical Record against the PBM Formulary Policy.
                    
                    RULES:
                    1. If patient meets ALL policy criteria -> "APPROVED".
                    2. If patient explicitly fails a criterion -> "DENIED".
                    3. If policy requires information missing from Patient PDF -> "PENDING_INFO".
                    
                    Output strictly as JSON:
                    {
                      "patient_status": "Brief status (e.g. Stable, Routine)",
                      "primary_diagnosis": "Full condition name",
                      "icd_10_code": "Billing code",
                      "requested_drug": "Medication requested",
                      "missing_info": "List missing data or 'None'",
                      "decision": "APPROVED", "DENIED", or "PENDING_INFO",
                      "reasoning": "1-2 short sentences explaining why.",
                      "message_to_provider": "Draft request to doctor if PENDING_INFO, else 'N/A'"
                    }
                    """
                    
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=[patient_part, policy_part, prompt]
                    )
                    
                    st.session_state.extracted_data = json.loads(response.text)
                except Exception as e:
                    st.error(f"Execution Error: {e}")

# --- 3. MAIN DASHBOARD ---
st.markdown('<h3 style="color: #334155;">Adjudication Results</h3>', unsafe_allow_html=True)

if st.session_state.extracted_data:
    data = st.session_state.extracted_data
    
    # COMPACT DECISION BANNER
    decision = data.get("decision", "UNKNOWN")
    box_class = "approved" if decision == "APPROVED" else "denied" if decision == "DENIED" else "pending"
    icon = "✅" if decision == "APPROVED" else "❌" if decision == "DENIED" else "⚠️"
    
    st.markdown(f"""
        <div class="decision-banner {box_class}">
            <div style="font-size: 2rem;">{icon}</div>
            <div>
                <h2>{decision}</h2>
                <p><strong>Rationale:</strong> {data.get('reasoning', '')}</p>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # COMPACT METRICS GRID
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("ICD-10 Code", data.get("icd_10_code", "N/A"))
    with col2: st.metric("Requested Rx", data.get("requested_drug", "N/A"))
    with col3: st.metric("Patient Status", data.get("patient_status", "N/A"))
    with col4: st.metric("Missing Info", "Yes" if data.get("missing_info", "None").lower() not in ["none", "n/a"] else "No")
    
    st.write("") # Tiny spacer
    
    # ACTION ITEM (If Pending)
    if decision == "PENDING_INFO":
        st.info(f"**📠 Auto-Drafted Fax to Provider:** {data.get('message_to_provider', 'N/A')}", icon="✉️")
    elif decision == "DENIED":
        st.error(f"**🚫 Denial Note:** Patient explicitly failed criteria. No further info requested.", icon="🚫")
    else:
        st.success(f"**✅ Approval Note:** All formulary criteria met. Ready for claim processing.", icon="✅")
        
    # DEVELOPER ACCORDION (Kept small and out of the way)
    with st.expander("Show Raw Developer Payload (JSON)"):
        st.json(data)
        
else:
    st.markdown("""
        <div style="padding: 40px; text-align: center; border: 2px dashed #cbd5e1; border-radius: 8px; color: #64748b;">
            <p style="margin:0; font-size: 1.1rem;">Upload Patient and Policy PDFs in the sidebar to run adjudication.</p>
        </div>
    """, unsafe_allow_html=True)
