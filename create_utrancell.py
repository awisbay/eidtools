import streamlit as st
import pandas as pd
import re
import os
import io
import zipfile
from datetime import datetime

def read_excel_file(file, sheet_names_to_try=None):
    """
    Read the Excel file and return a pandas DataFrame
    Tries to read from "UMTS_2100" or "U2100" sheets
    """
    if sheet_names_to_try is None:
        sheet_names_to_try = ["UMTS_2100", "U2100"]
    
    # Try each sheet name
    for sheet_name in sheet_names_to_try:
        try:
            #st.write("Trying to read All 2100 Sheet")
            df = pd.read_excel(file, sheet_name=sheet_name)
            st.success(f"Successfully read sheet '{sheet_name}' with    {len(df) - 1} Utrancell")
            return df
        except ValueError as e:
            if "No sheet named" in str(e):
                st.warning(f"Sheet '{sheet_name}' not found, Please check CDD Data..")
            else:
                st.warning(f"sheet '{sheet_name}' Not found in this file")
        except Exception as e:
            st.warning(f"Failed to read sheet '{sheet_name}': {e}")
    
    raise ValueError("Failed to read any sheet from the Excel file")

def read_template_file(file_path):
    """
    Read the template file and return its contents as a string
    """
    print(f"Reading template file: {file_path}")
    with open(file_path, 'r') as file:
        content = file.read()
    print(f"Template file read successfully with {len(content)} characters")
    return content

def create_mapping():
    """
    Create a mapping from placeholders to Excel headers
    Initial mapping as specified by the user
    """
    # Map template placeholders to Excel column headers
    mapping = {
        # Initial mapping as specified by the user
        'iublink' : 'IuB Link Name',
        'rnc' : 'RNC',
        'LAC' : 'LAC',
        'URA' : 'URA',
        'utrancell' : 'UtrancellID',
        'Cellid' : 'CID',
        'RAC' : 'RAC',
        'rbsid' : 'RBS ID',
        'earfcnul' : 'UUARFCN',
        'earfcndl' : 'DUARFCN',
        'scrambling' : 'primaryScramblingCode',
        'longitude' : 'WGS84-Long',
        'latitude' : 'WGS84-Lat',
        'tcell' : 'tCell',
        'iphost' : "Technology"
    }
    
    return mapping

def find_placeholders(template):
    """
    Find all placeholders in the template (in the format {placeholder})
    """
    placeholders = re.findall(r'\{([^}]+)\}', template)
    return set(placeholders)

def generate_scripts_by_rnc(df, template, mapping):
    """
    Generate scripts grouped by RNC, excluding rows where RNC='planning'
    """
    scripts_by_rnc = {}
    
    # Ensure the RNC column exists
    if mapping['rnc'] not in df.columns:
        raise ValueError(f"RNC column '{mapping['rnc']}' not found in the Excel file")
    
    # Convert RNC column to string to ensure proper grouping
    df[mapping['rnc']] = df[mapping['rnc']].astype(str)
    
    # Filter out rows where RNC is "planning"
    df_filtered = df[df[mapping['rnc']].str.lower() != "planning"]
    
    # Progress bar for processing
    progress_bar = st.progress(0)
    
    # Group by RNC
    rnc_groups = list(df_filtered.groupby(mapping['rnc']))
    total_rncs = len(rnc_groups)
    
    for i, (rnc, group) in enumerate(rnc_groups):
        st.write(f"Processing RNC: {rnc} with {len(group)} cells")
        
        # This will store all cell scripts for this RNC
        rnc_script = ""
        
        # Process each row in the group (each UTRAN cell)
        for _, row in group.iterrows():
            # Create a copy of the template for this row
            row_script = template
            
            # Replace placeholders based on mapping
            for placeholder, header in mapping.items():
                if header is not None and header in df.columns:
                    # Get the value and ensure it's a string
                    value = str(row[header]) if pd.notna(row[header]) else ""
                    # Replace all instances of the placeholder
                    row_script = row_script.replace(f"{{{placeholder}}}", value)
            
            # Add the processed script for this cell
            if rnc_script:
                rnc_script += "\n\n"
            rnc_script += row_script
        
        # Store the complete script for this RNC
        if rnc_script:
            scripts_by_rnc[rnc] = rnc_script
        
        # Update progress bar
        progress_bar.progress((i + 1) / total_rncs)
    
    return scripts_by_rnc

def write_scripts_to_files(scripts_by_rnc):
    """
    Write the generated scripts to files with format {rnc}_MOCN_{DDMMYYYY}
    """
    date_str = datetime.now().strftime('%d%m%Y')
    rncs_processed = []
    
    for rnc, script in scripts_by_rnc.items():
        filename = f"{rnc}_MOCN_{date_str}.txt"
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(script)
        print(f"Created script file: {filename} ({os.path.getsize(filename)} bytes)")
        rncs_processed.append(rnc)
    
    return rncs_processed

def main():
    st.title("3G MOCN Utrancell Script")
    st.write("Upload your Excel file and template file to generate Utrancell scripts.")
    
    # File uploads
    excel_file = st.file_uploader("Upload Excel file", type=["xlsx", "xls"])
    template_file = "template_script.txt"
    
    # Custom sheet name input
    sheet_names = ["UMTS_2100", "U2100"]
    
    if excel_file and template_file:
        if st.button("Generate Scripts"):
            st.write("Processing files...")
            
            try:
                # Read Excel file
                df = read_excel_file(excel_file, sheet_names)
                
                # Read template file
                with open("template_script.txt", "r", encoding="utf-8") as template:
                    # Read the contents of the file
                    template_content = template.read()
                #st.success(f"Template file read successfully with {len(template_content)} characters")
                
                # Find all placeholders in the template
                placeholders = find_placeholders(template_content)
               
                # Create mapping from placeholders to Excel headers
                mapping = create_mapping()
                
                # Check for missing columns in DataFrame
                missing_cols = []
                for placeholder, header in mapping.items():
                    if header is not None and header not in df.columns:
                        missing_cols.append(f"{placeholder} -> {header}")
                        st.warning(f"Column '{header}' for placeholder '{placeholder}' not found in Excel")
                
                # Generate scripts by RNC
                scripts_by_rnc = generate_scripts_by_rnc(df, template_content, mapping)
                
                if scripts_by_rnc:
                    st.success(f"Script generation completed for {len(scripts_by_rnc)} RNCs.")
                    
                    # Get current date for file naming
                    date_str = datetime.now().strftime('%d%m%Y')
                    
                    # If we have multiple RNCs, create a zip file
                    if len(scripts_by_rnc) > 1:
                        # Create a zip file in memory
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED) as zip_file:
                            for rnc, script in scripts_by_rnc.items():
                                file_name = f"{rnc}_MOCN_{date_str}.txt"
                                zip_file.writestr(file_name, script)
                        
                        # Reset buffer position
                        zip_buffer.seek(0)
                        
                        # Create download button for the zip file
                        st.download_button(
                            label="📥 Download All Scripts as ZIP",
                            data=zip_buffer,
                            file_name=f"3G_MOCN_{date_str}.zip",
                            mime="application/zip"
                        )
                    
                    # Create individual download buttons for each script
                    st.write("### Individual Script Files:")
                    for rnc, script in scripts_by_rnc.items():
                        file_name = f"{rnc}_MOCN_{date_str}.txt"
                        st.download_button(
                            label=f"📄 Download {file_name}",
                            data=script,
                            file_name=file_name,
                            mime="text/plain",
                            key=f"btn_{rnc}"
                        )
                else:
                    st.error("No scripts were generated. Check if your Excel file contains valid RNC data.")
            
            except Exception as e:
                st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()


