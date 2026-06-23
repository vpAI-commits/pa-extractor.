import streamlit as st
from google import genai
from google.genai import types
import json
import time

# --- 1. WORKSPACE UI CONFIGURATION ---
st.set_page_config(page_title="PA Agent Console", page_icon="🧬", layout="centered")

if "extracted_data" not in st.session_state:
    st.session_state.extracted_data = None

# Custom CSS for the Immersive Agentic Workspace
st.markdown("""
    <style>
    /* Sleek Dark Minimalist Theme */
    .stApp { 
        background-color: #09090b; 
        color: #fafafa; 
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide default elements */
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    
    /* Clean, focused headers */
    h1 { font-weight: 800; letter-spacing: -1px; margin-bottom: 0px; }
    h2, h3, h4 { font-weight: 600; color: #e4e4e7; }
    
    /* Subtle file uploaders */
    .stFileUploader > div > div {
        background-color: #18181b;
        border: 1px solid #27272a;
        border-radius: 12px;
        transition: border 0.3s ease;
    }
    .stFileUploader > div > div:hover {
        border: 1px solid #6366f1;
    }
    
    /* Action Button */
    div.stButton > button:first-child {
        background-color: #fafafa;
        color: #09090b;
        border-radius: 8px;
        border: none;
        padding: 12px;
        font-weight: 600;
        transition: transform 0.2s ease;
        width: 100%;
    }
    div.stButton > button:first-child:hover {
        transform: translateY(-2px);
        background-color: #e4e4e7;
        color: #09090b;
    }

    /* The Report Document Style */
    .report-card {
        background-color: #18181b;
        border: 1px solid #27272a;
        border-radius: 16px;
        padding: 40px;
        margin-top: 20px;
        box-shadow: 0 20px 40px rgba(0,0,0,0.4);
    }
    .report-header {
        border-bottom: 1px solid #27272a;
        padding-bottom: 20px;
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .status-badge {
        padding: 6px 16px;
        border-radius: 999px;
        font-weight: 700;
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .status-approved { background-color: rgba(34, 197, 94, 0.1); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.2); }
    .status-denied { background-color: rgba(239, 68, 68, 0.1); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.2); }
    .status-pending { background-color: rgba(245, 158, 11, 0.1); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.2); }
    
    .data-row {
        display: flex;
        margin-bottom: 15px;
    }
    .data-label {
        width: 150px;
        color: #a1a1aa;
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .data-value {
        flex: 1;
        color: #fafafa;
        font-weight: 500;
    }
    
    .rationale-box {
        background-color: #09090b;
        border-left: 4px solid #6366f1;
        padding: 20px;
        margin-top: 30px;
        border-radius: 0 8px 8px 0;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. HEADER AREA ---
st.markdown('<h1>Autonomous Adjudicator</h1>', unsafe_allow_html=True)
st.markdown('<p style="color: #a1a1aa; font-size: 16px;">Secure clinical reasoning engine. Upload requisite documentation to initiate the review cycle.</p>', unsafe_allow_html=True)
st.write("")

# --- 3. THE UPLOAD GRID (No Sidebar) ---
col1, col2 = st.columns(2, gap="large")
with col1:
    st.markdown("#### 1. Patient Chart")
    patient_file = st.file_uploader("Upload PDF", type=["pdf"], label_visibility="collapsed", key="pat")
with col2:
    st.markdown("#### 2. PBM Formulary")
    policy_file = st.file_uploader("Upload PDF", type=["pdf"], label_visibility="collapsed", key="pol")

st.write("")
st.write("")

# --- 4. EXECUTION FLOW ---
if patient_file and policy_file:
    if st.button("Initialize Reasoning Agent"):
        
        # The new immersive "Agent Working" UX
        with st.status("Initializing clinical review protocol...", expanded=True) as status:
            try:
                st.write("📥 Loading documents into memory cache...")
                patient_bytes = patient_file.read()
                policy_bytes = policy_file.read()
                time.sleep(0.5) # Slight delay for UX effect
                
                st.write("🔐 Authenticating with Gemini API...")
                client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
                
                patient_part = types.Part.from_bytes(data=patient_bytes, mime_type='application/pdf')
                policy_part = types.Part.from_bytes(data=policy_bytes, mime_type='application/pdf')
                
                st.write("🧠 Cross-referencing patient history against formulary criteria...")
                prompt = """
                You are a strict PBM Clinical Pharmacist Adjudicator.
                Evaluate the provided Patient Medical Record against the PBM Formulary Policy.
                
                RULES:
                1. If patient meets ALL policy criteria -> "APPROVED".
                2. If patient explicitly fails a criterion -> "DENIED".
                3. If policy requires information missing from Patient PDF -> "PENDING_INFO".
                
                Output strictly as JSON:
                {
                  "patient_status": "Brief status",
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
                
                st.write("📝 Formatting final clinical determination...")
                st.session_state.extracted_data = json.loads(response.text)
                
                status.update(label="Adjudication complete.", state="complete", expanded=False)
                
            except Exception as e:
                status.update(label="Execution failed.", state="error", expanded=True)
                st.error(f"System Error: {e}")

# --- 5. THE FORMAL REPORT UI ---
if st.session_state.extracted_data:
    data = st.session_state.extracted_data
    decision = data.get("decision", "UNKNOWN")
    
    status_class = "status-approved" if decision == "APPROVED" else "status-denied" if decision == "DENIED" else "status-pending"
    display_decision = decision.replace("_", " ")

    st.markdown(f"""
        <div class="report-card">
            <div class="report-header">
                <h2 style="margin: 0;">Clinical Determination Report</h2>
                <div class="status-badge {status_class}">{display_decision}</div>
            </div>
            
            <div class="data-row">
                <div class="data-label">Requested Rx</div>
                <div class="data-value">{data.get('requested_drug', 'N/A')}</div>
            </div>
            <div class="data-row">
                <div class="data-label">Diagnosis</div>
                <div class="data-value">{data.get('primary_diagnosis', 'N/A')} (ICD-10: {data.get('icd_10_code', 'N/A')})</div>
            </div>
            <div class="data-row">
                <div class="data-label">Patient Status</div>
                <div class="data-value">{data.get('patient_status', 'N/A')}</div>
            </div>
            <div class="data-row">
                <div class="data-label">Missing Data</div>
                <div class="data-value">{data.get('missing_info', 'None')}</div>
            </div>
            
            <div class="rationale-box">
                <div class="data-label" style="margin-bottom: 8px;">Adjudicator Rationale</div>
                <div style="color: #e4e4e7; font-size: 16px; line-height: 1.5;">{data.get('reasoning', '')}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.write("")
    
    # Handle the Provider Message if Pending
    if decision == "PENDING_INFO":
        st.markdown("#### ✉️ Drafted Provider Outreach")
        st.info(data.get('message_to_provider', 'N/A'))
        
    st.write("")
    with st.expander("View Raw System Output"):
        st.json(data)
