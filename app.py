import streamlit as st
from google import genai
from google.genai import types
import json

# --- 1. APPLE UI CONFIGURATION ---
st.set_page_config(page_title="PA Nexus", page_icon="", layout="wide", initial_sidebar_state="expanded")

if "extracted_data" not in st.session_state:
    st.session_state.extracted_data = None

# Custom CSS for Apple's Design Language
st.markdown("""
    <style>
    /* Base Apple OS Font and Background */
    .stApp { 
        background-color: #F5F5F7; 
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", Roboto, Helvetica, Arial, sans-serif; 
        color: #1D1D1F; 
    }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    
    /* Typography Overrides */
    h1, h2, h3, h4 { font-weight: 600; letter-spacing: -0.015em; color: #1D1D1F; }
    p { color: #86868B; }
    
    /* Apple Pill Buttons */
    div.stButton > button:first-child {
        background-color: #0071E3; /* Apple Blue */
        color: white;
        border-radius: 980px; /* Perfect pill shape */
        border: none;
        padding: 12px 28px;
        font-weight: 400;
        font-size: 17px;
        transition: all 0.2s ease;
    }
    div.stButton > button:first-child:hover {
        background-color: #0077ED;
        transform: scale(1.02);
    }
    
    /* Smooth Floating Metric Cards */
    div[data-testid="metric-container"] { 
        background-color: #FFFFFF; 
        border: none;
        border-radius: 20px; 
        padding: 24px; 
        box-shadow: 0 4px 24px rgba(0,0,0,0.04);
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
    }
    div[data-testid="stMetricLabel"] { 
        color: #86868B; 
        font-size: 12px; 
        font-weight: 600; 
        text-transform: uppercase; 
        letter-spacing: 0.08em; 
        margin-bottom: 8px;
    }
    div[data-testid="stMetricValue"] { 
        color: #1D1D1F; 
        font-size: 36px; 
        font-weight: 600; 
        letter-spacing: -0.02em; 
    }
    
    /* Massive, Clean Decision Box */
    .apple-banner { 
        background-color: #FFFFFF; 
        border-radius: 24px; 
        padding: 40px; 
        display: flex; 
        flex-direction: column; 
        align-items: center; 
        text-align: center; 
        box-shadow: 0 10px 40px rgba(0,0,0,0.06); 
        margin-bottom: 30px;
    }
    .apple-banner.approved { border-top: 6px solid #34C759; } /* Apple OS Green */
    .apple-banner.denied { border-top: 6px solid #FF3B30; } /* Apple OS Red */
    .apple-banner.pending { border-top: 6px solid #FF9500; } /* Apple OS Orange */
    
    .banner-title { font-size: 48px; font-weight: 700; letter-spacing: -0.02em; margin: 0; color: #1D1D1F; }
    .banner-rationale { font-size: 19px; color: #86868B; margin-top: 12px; max-width: 600px; line-height: 1.4; }
    </style>
""", unsafe_allow_html=True)

# --- 2. SIDEBAR: CLEAN UPLOAD ---
with st.sidebar:
    st.markdown('<h2 style="margin-top:0;">PA Nexus</h2>', unsafe_allow_html=True)
    st.markdown("<p style='font-size:14px; margin-top:-10px;'>Adjudication, engineered for tomorrow.</p>", unsafe_allow_html=True)
    st.write("")
    
    st.markdown("<p style='font-weight:600; color:#1D1D1F; margin-bottom:0;'>Patient Record</p>", unsafe_allow_html=True)
    patient_file = st.file_uploader("Upload Medical PDF", type=["pdf"], label_visibility="collapsed", key="pat")
    
    st.write("")
    
    st.markdown("<p style='font-weight:600; color:#1D1D1F; margin-bottom:0;'>PBM Policy</p>", unsafe_allow_html=True)
    policy_file = st.file_uploader("Upload Policy PDF", type=["pdf"], label_visibility="collapsed", key="pol")
    
    st.write("")
    st.write("")
    
    if patient_file and policy_file:
        if st.button("Run Adjudication", use_container_width=True):
            with st.spinner("Analyzing securely..."):
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
                    
                    st.session_state.extracted_data = json.loads(response.text)
                except Exception as e:
                    st.error(f"Error: {e}")

# --- 3. MAIN DASHBOARD ---
if st.session_state.extracted_data:
    data = st.session_state.extracted_data
    
    # APPLE-STYLE HERO BANNER
    decision = data.get("decision", "UNKNOWN")
    box_class = "approved" if decision == "APPROVED" else "denied" if decision == "DENIED" else "pending"
    
    # Map the text to something slightly more elegant
    display_decision = "Authorized." if decision == "APPROVED" else "Declined." if decision == "DENIED" else "Action Required."
    
    st.markdown(f"""
        <div class="apple-banner {box_class}">
            <h1 class="banner-title">{display_decision}</h1>
            <p class="banner-rationale">{data.get('reasoning', '')}</p>
        </div>
    """, unsafe_allow_html=True)
    
    # CENTERED METRIC CARDS
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("ICD-10", data.get("icd_10_code", "N/A"))
    with col2: st.metric("Requested Therapy", data.get("requested_drug", "N/A"))
    with col3: st.metric("Missing Labs/Data", "Yes" if data.get("missing_info", "None").lower() not in ["none", "n/a", "complete"] else "No")
    
    st.write("")
    st.write("")
    
    # ELEGANT ACTION ALERTS
    if decision == "PENDING_INFO":
        st.info(f"**Drafted Provider Communication:** {data.get('message_to_provider', 'N/A')}", icon="📨")
    elif decision == "DENIED":
        st.error(f"**Coverage Note:** Patient does not meet formulary requirements.", icon="🛑")
    else:
        st.success(f"**Coverage Note:** All prerequisites verified. Ready for switch transmission.", icon="✅")
        
    st.write("")
    with st.expander("Show Developer Payload"):
        st.json(data)
        
else:
    # APPLE EMPTY STATE
    st.markdown("""
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 60vh; text-align: center;">
            <h1 style="font-size: 56px; font-weight: 700; letter-spacing: -0.02em; margin-bottom: 10px;">Pro intelligence. <br> Zero friction.</h1>
            <p style="font-size: 21px; color: #86868B; max-width: 500px; line-height: 1.4;">
                Upload a patient record and policy document to instantly adjudicate clinical data.
            </p>
        </div>
    """, unsafe_allow_html=True)
