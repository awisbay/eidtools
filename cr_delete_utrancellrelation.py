import streamlit as st
import pandas as pd
import io
import base64
from datetime import datetime


# Custom CSS to improve the appearance
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .stButton button {
        width: 100%;
    }
    .output-area {
        background-color: #f0f2f6;
        border-radius: 5px;
        padding: 20px;
        margin: 10px 0;
    }
    h1, h2, h3 {
        color: #0e1117;
    }
</style>
""", unsafe_allow_html=True)

# App title and description
st.title("CR Delete")

date_str = datetime.now().strftime('%d%m%Y')

# Template definition``
template = """DELETE
FDN : {path}"""
cola, colb = st.columns(spec=2)

st.subheader("Upload a CR_S1 file")
# File uploader
uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx", "xls"])

if uploaded_file is not None:
    try:
        # Display file info
        file_details = {"Filename": uploaded_file.name, "File size": f"{uploaded_file.size/1024:.2f} KB"}
        # st.write("File Details:", file_details)
        
        # Read Excel file
        df = pd.read_excel(uploaded_file, sheet_name="DEL_UtranRelation")
        
        # Display preview of the dataframe
        # st.subheader("Preview of Excel Data")
        # st.dataframe(df.head())
        
        # Check if 'mo' column exists
        if 'mo' not in df.columns:
            st.error("The 'mo' column was not found in the DEL_UtranRelation sheet.")
        else:
            # Process the template
            output_text = ""
            record_count = 0
            
            for _, row in df.iterrows():
                # Replace {path} with the 'mo' column value
                command = template.replace("{path}", row['mo'])
                output_text += command + "\n\n"
                record_count += 1
            
            # Display results
            # st.subheader(f"Generated Commands ({record_count} records)")
            
            # with st.expander("Show all commands", expanded=True):
            #     st.text_area("", output_text, height=400)
            
            # Download button
            st.subheader("Download Results")
            
            # Create a download button for a text file
            txt_download = st.download_button(
                label="Download as TXT file",
                data=output_text,
                file_name=f"CR_S1_DEL_UtranRelation_CMBULK_{date_str}.txt",
                mime="text/plain"
            )
            
    except Exception as e:
        st.error(f"An error occurred while processing the file: {str(e)}")
else:
    # Display sample template
    st.warning('Please make sure sheet "DEL_UtranRelation" exist in Excel File')
    #st.code(template)

st.divider()
st.subheader("Upload a CR S3 File")
st.markdown("Still Under Construction 🪒 🏗 🏗 🏗")
    
    #st.info("Upload an Excel file to get started. The file should contain a sheet named 'DEL_UtranRelation' with a column named 'mo'.")

# Footer
#st.markdown("---")
#st.markdown("© 2025 FDN Template Processor")