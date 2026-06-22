import streamlit as st
from google import genai
from google.genai import types
import json

# --- 1. UI CONFIGURATION ---
st.set_page_config(page_title="PA Triage Portal", page_icon="🏥", layout="wide")

st.title("🏥 Enterprise Prior Auth Extractor")
st.markdown("Upload a patient medical document to automatically extract clinical metadata and standard ICD-10 billing codes.")
st.divider()

# --- 2. FILE UPLOADER UI ---
uploaded_file = st.file_uploader("Drop Patient Medical Record (PDF)", type=["pdf"])

if uploaded_file:
    st.success(f"File '{uploaded_file.name}' ready for processing.")
    
    # Create a nice wide button
    if st.button("🚀 Extract Clinical Data", use_container_width=True):
        
        # Show a loading spinner while the AI thinks
        with st.spinner("Analyzing document structure and extracting clinical entities..."):
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
                  "patient_status": "Brief 3 word health status",
                  "primary_diagnosis": "Condition name",
                  "icd_10_code": "Standard billing code",
                  "requested_drug": "Medication requested",
                  "missing_info": "List any missing lab results needed for approval"
                }
                """
                
                # Send to the Gemini model
                response = client.models.generate_content(
                    model='gemini-2.5-pro',
                    contents=[
                        types.Part.from_bytes(data=pdf_bytes, mime_type='application/pdf'),
                        prompt
                    ]
                )
                
                # Turn the text into readable data
                data = json.loads(response.text)
                
                # --- 3. BEAUTIFUL DASHBOARD UI ---
                st.divider()
                st.subheader("Extraction Results")
                
                # Create three columns for top-level metrics
                col1, col2, col3 = st.columns(3)
                col1.metric("ICD-10 Code", data.get("icd_10_code", "N/A"))
                col2.metric("Requested Drug", data.get("requested_drug", "N/A"))
                col3.metric("Patient Status", data.get("patient_status", "N/A"))
                
                st.write("") # Add some spacing
                
                # Create tabs for deeper details
                tab1, tab2 = st.tabs(["📝 Clinical Summary", "⚙️ Raw JSON Code"])
                
                with tab1:
                    st.info(f"**Primary Diagnosis:** {data.get('primary_diagnosis', 'N/A')}")
                    st.warning(f"**Missing Information (Action Required):** {data.get('missing_info', 'None')}")
                    
                with tab2:
                    st.json(data)
                    
            except Exception as e:
                st.error(f"An error occurred during extraction. Please ensure the PDF is readable. Error: {e}")
