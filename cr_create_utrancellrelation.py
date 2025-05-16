
import streamlit as st
import pandas as pd
import io
import zipfile
from datetime import datetime

# Define templates for each sheet type
TEMPLATES = {
    "Add_InternalUtranRelation": """CREATE
FDN : SubNetwork={RNC},MeContext={RNC},ManagedElement=1,RncFunction=1,UtranCell={sourcecell},UtranRelation={targetcell}
utranCellRef : "SubNetwork={RNC},MeContext={RNC},ManagedElement=1,RncFunction=1,UtranCell={targetcell}"
hcsSib11Config : {hcsPrio=0, qHcs=0, penaltyTime=0, temporaryOffset1=0, temporaryOffset2=0}
loadSharingCandidate : {loadsharing}
qOffset1sn : 0
qOffset2sn : {qoffset2sn}
selectionPriority : {selectionprio}
"""
    # Add more templates for other sheets as needed
    # "Another_Sheet_Name": "Another template...",
}

# Define field mappings for each sheet type
FIELD_MAPPINGS = {
    "Add_InternalUtranRelation": {
        "{RNC}": "RNC",
        "{sourcecell}": "SourceCell",
        "{targetcell}": "DestinationCell",
        "{loadsharing}": "loadSharingCandidate",
        "{qoffset2sn}": "qOffset2sn",
        "{selectionprio}": "selectionPriority"
    }
    # Add more field mappings for other sheets as needed
    # "Another_Sheet_Name": { ... },
}

def generate_config(df, sheet_name):
    """Generate configuration text from dataframe based on template for the selected sheet."""
    if sheet_name not in TEMPLATES:
        return f"No template defined for sheet: {sheet_name}"
    
    template = TEMPLATES[sheet_name]
    field_mapping = FIELD_MAPPINGS.get(sheet_name, {})
    config_parts = []
    
    for i, row in df.iterrows():
        # Skip rows with missing essential data (assuming RNC is always required)
        if pd.isna(row.get('RNC')):
            continue
        
        # Replace placeholders in template with values from dataframe
        config_part = template
        for placeholder, column_name in field_mapping.items():
            if column_name in row:
                # Handle different data types appropriately
                if isinstance(row[column_name], (int, float)) and not pd.isna(row[column_name]):
                    value = str(int(row[column_name]))  # Convert float to int if it's a number
                elif pd.isna(row[column_name]):
                    value = "0"  # Default value for missing numeric fields
                else:
                    value = str(row[column_name])
                
                config_part = config_part.replace(placeholder, value)
        
        config_parts.append(config_part)
    
    # Join all configurations with double line breaks
    return "\n\n".join(config_parts)

def generate_configs_by_rnc(df, sheet_name):
    """Generate configurations grouped by RNC."""
    if "RNC" not in df.columns:
        return {"ERROR": "RNC column not found in the sheet"}
    
    rnc_configs = {}
    
    # Group dataframe by RNC
    for rnc, group_df in df.groupby("RNC"):
        if pd.isna(rnc):
            continue
            
        config_text = generate_config(group_df, sheet_name)
        if config_text:
            rnc_configs[str(rnc)] = config_text
    
    return rnc_configs

def main():
    st.title("3G CR CMBulk Generator")
    st.write("This app generates CMBulk script from Excel data.")
    
    # File uploader for Excel file
    uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx", "xls"])
    
    if uploaded_file is not None:
        # Read all sheets in the Excel file
        xlsx = pd.ExcelFile(uploaded_file)
        sheet_names = xlsx.sheet_names
        
        # Allow user to select which sheet to process
        selected_sheet = st.selectbox("Select sheet to process", sheet_names)
        
        # Read the selected sheet
        df = pd.read_excel(uploaded_file, sheet_name=selected_sheet)
        
        # Display dataframe preview
        st.subheader(f"Data Preview: {selected_sheet}")
        st.dataframe(df.head())
        
        # Check if the sheet is empty (only has headers)
        if len(df) == 0:
            st.warning("⚠️ The selected sheet is empty (contains only headers). No configuration can be generated.")
        
        # Check if we have a template for this sheet
        if selected_sheet in TEMPLATES:
            # Generate button
            if st.button("Generate Configuration"):
                if df.empty:
                    st.error("No data found in the selected sheet.")
                    st.stop()
                
                # Get current date for filename
                current_date = datetime.now().strftime('%Y%m%d')
                
                # Group configurations by RNC
                rnc_configs = generate_configs_by_rnc(df, selected_sheet)
                
                if not rnc_configs:
                    st.warning("No valid data found to generate configurations.")
                    st.stop()
                
                # If there's only one RNC, provide direct download
                if len(rnc_configs) == 1:
                    rnc = list(rnc_configs.keys())[0]
                    config_text = rnc_configs[rnc]
                    
                    # Create filename with RNC and sheet name
                    filename = f"{rnc}_{selected_sheet}_{current_date}.txt"
                    
                    # Display preview
                    st.subheader(f"Configuration Preview for RNC: {rnc}")
                    st.text_area("Preview", config_text, height=300)
                    
                    # Download button
                    st.download_button(
                        label=f"Download Configuration for {rnc}",
                        data=config_text,
                        file_name=filename,
                        mime="text/plain"
                    )
                
                # If there are multiple RNCs, create a zip file
                else:
                    # Create in-memory zip file
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                        for rnc, config_text in rnc_configs.items():
                            # Create filename with RNC and sheet name
                            filename = f"{rnc}_{selected_sheet}_{current_date}.txt"
                            zip_file.writestr(filename, config_text)
                    
                    zip_buffer.seek(0)
                    
                    # Display the RNCs found
                    st.subheader(f"Multiple RNCs Found: {', '.join(rnc_configs.keys())}")
                    st.info(f"A zip file containing separate configuration files for each RNC will be created.")
                    
                    # Let user see a preview of one of the configs
                    preview_rnc = st.selectbox("Select RNC to preview:", list(rnc_configs.keys()))
                    st.text_area(f"Preview for RNC: {preview_rnc}", rnc_configs[preview_rnc], height=300)
                    
                    # Download button for zip file
                    st.download_button(
                        label="Download Script (ZIP) 📦",
                        data=zip_buffer,
                        file_name=f"All_RNCs_{selected_sheet}_{current_date}.zip",
                        mime="application/zip"
                    )
        else:
            st.warning(f"No template defined for sheet: {selected_sheet}")
            st.info("Available templates: " + ", ".join(TEMPLATES.keys()))
    else:
        st.info("Please upload an Excel file to generate configurations.")

if __name__ == "__main__":
    main()