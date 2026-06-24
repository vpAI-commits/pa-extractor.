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
    
    /* Process Trace Styling */
    .trace-step {
        background-color: rgba(99, 102, 241, 0.05);
        border-left: 2px solid #6366f1;
        padding: 10px 15px;
        margin-bottom: 10px;
        font-size: 14.5px;
        color: #e4e4e7;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. HEADER AREA ---
st.markdown('<h1>Autonomous Adjudicator</h1>', unsafe_allow_html=True)
st.markdown('<p style="color: #a1a1aa; font-size: 16px;">Secure clinical reasoning engine. Upload requisite documentation to initiate the review cycle.</p>', unsafe_allow_html=True)
st.write("")

# --- 3. THE UPLOAD GRID ---
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
        
        # The immersive "Agent Working" UX
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
                
                # UPGRADED PROMPT: Now forces the AI to document its step-by-step logic
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
                  "step_by_step_analysis": [
                    "Step 1 (Extraction): Detail exactly what clinical data was found in the patient record.",
                    "Step 2 (Policy Lookup): Detail the exact policy rules found for the requested drug.",
                    "Step 3 (Adjudication Mapping): Explain exactly how the clinical data maps to the rules to reach the final decision."
                  ],
                  "decision": "APPROVED", "DENIED", or "PENDING_INFO",
                  "reasoning": "1-2 short sentences summarizing the decision.",
                  "message_to_provider": "Draft request to doctor if PENDING_INFO, else 'N/A'"
                }
                """
                
                # --- ADVANCED ERROR HANDLING & LONGER BACKOFF ---
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
                            wait_time = 5 * (attempt + 1) # Waits 5s, then 10s to clear Google limits
                            st.write(f"⚠️ **Google API Speed Limit.** Pausing for {wait_time}s to cool down... (Attempt {attempt + 1}/{max_retries})")
                            add_log(f"429 Resource Exhausted. Retrying in {wait_time}s...", "warning")
                            
                            if attempt < max_retries - 1:
                                time.sleep(wait_time)
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
                                time.sleep(3)
                                continue
                            else:
                                raise RuntimeError(f"Google Gemini Servers failed to respond after {max_retries} attempts.")

                # Ensure we got a response
                if not response_text:
                    raise RuntimeError("Failed to generate content. The response was empty.")

                st.write("📝 Formatting final clinical determination...")
                add_log("Applying JSON extraction layer...", "info")
                
                # --- ROBUST JSON EXTRACTION ---
                try:
                    clean_text = response_text.strip()
                    if clean_text.startswith("```json"):
                        clean_text = clean_text[7:]
                    elif clean_text.startswith("```"):
                        clean_text = clean_text[3:]
                    if clean_text.endswith("```"):
                        clean_text = clean_text[:-3]
                    clean_text = clean_text.strip()
                    
                    st.session_state.extracted_data = json.loads(clean_text)
                    add_log("JSON parsed and validated.", "success")
                    
                except json.JSONDecodeError as json_err:
                    add_log(f"JSON Parse Failure: {json_err}", "error")
                    add_log(f"Raw Output: {response_text}", "warning")
                    raise ValueError("The AI model returned improperly formatted JSON data. Please try again.")
                
                status.update(label="Adjudication complete.", state="complete", expanded=False)
                
            except Exception as e:
                status.update(label="Execution aborted.", state="error", expanded=True)
                add_log(f"Critical System Error: {str(e)}", "error")
                st.error(f"System Error: {e}")

# --- 5. THE FORMAL REPORT UI ---
if st.session_state.extracted_data:
    data = st.session_state.extracted_data
    decision = data.get("decision", "UNKNOWN")
    
    status_class = "status-approved" if decision == "APPROVED" else "status-denied" if decision == "DENIED" else "status-pending"
    display_decision = decision.replace("_", " ")

    # FIX: Flattened HTML string to prevent Streamlit's Markdown parser from turning it into a code block
    report_html = f"""<div class="report-card">
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
</div>"""

    st.markdown(report_html, unsafe_allow_html=True)

    st.write("")
    
    # Render the new Step-by-Step Adjudication Trace
    analysis_steps = data.get('step_by_step_analysis', [])
    if analysis_steps:
        with st.expander("🔍 Adjudication Process Trace", expanded=True):
            for step in analysis_steps:
                st.markdown(f'<div class="trace-step">{step}</div>', unsafe_allow_html=True)
                
    st.write("")
    
    # Handle the Provider Message if Pending
    if decision == "PENDING_INFO":
        st.markdown("#### ✉️ Drafted Provider Outreach")
        st.info(data.get('message_to_provider', 'N/A'))
        
    st.write("")
    with st.expander("View Raw System Output (JSON)"):
        st.json(data)

# --- 6. DIAGNOSTIC LOGS UI ---
st.write("---")
with st.expander("📟 System Diagnostics & Logs"):
    if st.session_state.get("system_logs"):
        for log in st.session_state.system_logs:
            color = "#4ade80" if log['level'] == "success" else "#f87171" if log['level'] == "error" else "#fbbf24" if log['level'] == "warning" else "#a1a1aa"
            st.markdown(f"<div style='color:{color}; font-family:monospace; font-size:13px; margin-bottom:4px;'>[{log['time']}] [{log['level'].upper()}] {log['msg']}</div>", unsafe_allow_html=True)
    else:
        st.markdown("<span style='color:#a1a1aa; font-family:monospace; font-size:13px;'>No logs recorded in this session.</span>", unsafe_allow_html=True)
