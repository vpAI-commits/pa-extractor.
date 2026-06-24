import streamlit as st
from google import genai
from google.genai import types
import json
import time
import re

# --- 1. WORKSPACE UI CONFIGURATION ---
st.set_page_config(page_title="PA Agent Console", page_icon="🧬", layout="centered")

if "extracted_data" not in st.session_state:
    st.session_state.extracted_data = None

if "system_logs" not in st.session_state:
    st.session_state.system_logs = []

def add_log(message, level="info"):
    """Helper to append system logs to the session state"""
    timestamp = time.strftime("%H:%M:%S")
    st.session_state.system_logs.append({"time": timestamp, "msg": message, "level": level})

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
        
        st.session_state.system_logs = [] # Clear previous logs
        add_log("System initialized. Review cycle starting.", "info")
        
        # The new immersive "Agent Working" UX
        with st.status("Initializing clinical review protocol...", expanded=True) as status:
            try:
                st.write("📥 Loading documents into memory cache...")
                add_log("Reading PDF bytes into memory...", "info")
                patient_bytes = patient_file.read()
                policy_bytes = policy_file.read()
                
                # Input Validation
                if not patient_bytes or not policy_bytes:
                    raise ValueError("Empty file detected. Please re-upload valid PDF documents.")
                    
                time.sleep(0.5) 
                
                st.write("🔐 Authenticating with Gemini API...")
                add_log("Authenticating Google API credentials...", "info")
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
                
                # --- ADVANCED ERROR HANDLING & EXPONENTIAL BACKOFF ---
                max_retries = 3
                response_text = None
                
                for attempt in range(max_retries):
                    try:
                        add_log(f"Attempt {attempt + 1}: Transmitting multi-modal payload...", "info")
                        response = client.models.generate_content(
                            model='gemini-2.5-flash',
                            contents=[patient_part, policy_part, prompt]
                        )
                        response_text = response.text
                        add_log("200 OK: Content generated successfully.", "success")
                        break # Success! Break the retry loop
                        
                    except Exception as api_err:
                        err_str = str(api_err).lower()
                        
                        # 1. Handle Rate Limits / Quotas (429)
                        if "429" in err_str or "resource_exhausted" in err_str or "quota" in err_str:
                            st.write(f"⚠️ **Google API Speed Limit (429).** Automatically pausing and retrying... (Attempt {attempt + 1}/{max_retries})")
                            add_log(f"429 Resource Exhausted. Retrying in {2 ** (attempt + 1)}s...", "warning")
                            
                            if attempt < max_retries - 1:
                                time.sleep(2 ** (attempt + 1)) # Waits 2s, 4s, etc.
                                continue
                            else:
                                raise RuntimeError("API Quota Reached. Please wait 60 seconds before initiating another review cycle.")
                        
                        # 2. Handle Bad Payloads (400)
                        elif "400" in err_str or "invalid_argument" in err_str:
                            add_log(f"400 Bad Request: {api_err}", "error")
                            raise ValueError("Invalid PDF payload. The document might be corrupted, password-protected, or too massive for the AI's context window.")
                            
                        # 3. Handle Other/Server Errors (500/503)
                        else:
                            add_log(f"API Error: {api_err}", "error")
                            if attempt < max_retries - 1:
                                time.sleep(2)
                                continue
                            else:
                                raise RuntimeError(f"Google Gemini Servers failed to respond after {max_retries} attempts.")

                # Ensure we got a response
                if not response_text:
                    raise RuntimeError("Failed to generate content. The response was empty.")

                st.write("📝 Formatting final clinical determination...")
                add_log("Applying Regex JSON extraction layer...", "info")
                
                # --- ROBUST JSON EXTRACTION ---
                try:
                    # Strips out markdown syntax in case the AI hallucinates code blocks
                    clean_text = re.sub(r'
