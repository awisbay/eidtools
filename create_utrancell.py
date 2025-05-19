import streamlit as st
import pandas as pd
import re
import os
import io
from io import BytesIO
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
        'cellid' : 'CID',
        'RAC' : 'RAC',
        'rbsid' : 'RBS ID',
        'earfcnul' : 'UUARFCN',
        'earfcndl' : 'DUARFCN',
        'scrambling' : 'primaryScramblingCode',
        'longitude' : 'WGS84-Long',
        'latitude' : 'WGS84-Lat',
        'tcell' : 'tCell',
        'iphost' : "Technology",
        'servicearea' : 'SAC',
        'localcellid' : 'localCellID',
        'maxtranspwr' : 'maximumTransmissionPower',
        'cpichpower' : 'primaryCpichPower'
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

def generate_content(df):
    text_file_content = []
    text_area_preview = []

    for _, row in df.iterrows():
        rnc = row['RNC']
        utrancell = row['UtranCellId']

        # Format for the text file
        text_file_content.append(f"SET\nFDN : SubNetwork={rnc},MeContext={rnc},ManagedElement=1,RncFunction=1,UtranCell={utrancell}\nadministrativeState : 0\n\n")
        text_file_content.append(f"SET\nFDN : SubNetwork={rnc},MeContext={rnc},ManagedElement=1,RncFunction=1,UtranCell={utrancell},Fach=1\nadministrativeState : 0\n\n")
        text_file_content.append(f"SET\nFDN : SubNetwork={rnc},MeContext={rnc},ManagedElement=1,RncFunction=1,UtranCell={utrancell},Hsdsch=1\nadministrativeState : 0\n\n")
        text_file_content.append(f"SET\nFDN : SubNetwork={rnc},MeContext={rnc},ManagedElement=1,RncFunction=1,UtranCell={utrancell},Hsdsch=1,Eul=1\nadministrativeState : 0\n\n")
        text_file_content.append(f"SET\nFDN : SubNetwork={rnc},MeContext={rnc},ManagedElement=1,RncFunction=1,UtranCell={utrancell},Pch=1\nadministrativeState : 0\n\n")
        text_file_content.append(f"SET\nFDN : SubNetwork={rnc},MeContext={rnc},ManagedElement=1,RncFunction=1,UtranCell={utrancell},Rach=1\nadministrativeState : 0\n\n")
        text_file_content.append(f"DELETE\nFDN : SubNetwork={rnc},MeContext={rnc},ManagedElement=1,RncFunction=1,UtranCell={utrancell}\n\n")
        # Format for the text area preview
        text_area_preview.append(f"cmedit delete SubNetwork={rnc},MeContext={rnc},ManagedElement=1,RncFunction=1,UtranCell={utrancell} --FORCE --ALL\n")

    # Join the preview content for display in the text area
    text_area_content = "\n".join(text_area_preview)

    return text_file_content, text_area_content

def create_zip_file(rnc_list, text_file_content):
    # Create a buffer to store the zip content
    zip_buffer = BytesIO()

    # Create a zip file in the buffer
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for rnc in rnc_list:
            filename = f"{rnc}_Delete_Utrancell_{datetime.now().strftime('%Y%m%d')}.txt"
            zipf.writestr(filename, "".join(text_file_content))

    # Seek to the start of the buffer before returning
    zip_buffer.seek(0)
    return zip_buffer

def main():
    st.title(":rainbow[3G MOCN Utrancell Script]")
    st.subheader(":green[Upload your CDD file to generate Utrancell scripts.]")

    # File uploads
    excel_file = st.file_uploader("Upload CDD Excel file", type=["xlsx", "xls"])
    #template_file = "template_script.txt"
    # Custom sheet name input
    sheet_names = ["UMTS_2100", "U2100"]

    # select template
    template_folder = "template_utrancell"  # example folder
    template_path = os.path.join(os.getcwd(), template_folder)
    template_files = [f for f in os.listdir(template_path) if f.endswith(".txt")]


    if excel_file and template_files:
        selected_template = st.selectbox("Please select template to process", template_files)
        if st.button("Generate Scripts"):
            st.write("Processing files...")

            try:
                # Read Excel file
                df = read_excel_file(excel_file, sheet_names)

                selected_template_path = os.path.join(template_path, selected_template)
                # Read template file
                with open(selected_template_path, "r", encoding="utf-8") as template:
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

    st.markdown("""
    <div style='height: 6px; background-color: pink; margin: 40px 0;'></div>
    """, unsafe_allow_html=True)
    st.subheader(":blue[Upload your PW file to generate Delete Utrancell scripts.]")
    excel_file_delete = st.file_uploader("Upload PW file", type=["xlsx", "xls"])


    if excel_file_delete is not None:
    # Read the Excel file
        xls = pd.ExcelFile(excel_file_delete)

    # Load the 'DEL_T-U21' sheet into a DataFrame
        if 'DEL_T-U21' in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name='DEL_T-U21')
            text_file_content, text_area_content = generate_content(df)

            # Get the unique RNC values
            rnc_list = df['RNC'].unique()

            # Generate filename based on RNC and date
            date_str = datetime.now().strftime('%Y%m%d')
            if len(rnc_list) > 1:
                # If more than 2 RNC values, create a zip file
                zip_buffer_cmbulk = create_zip_file(rnc_list, text_file_content)
                zip_buffer_cmedit = create_zip_file(rnc_list, text_area_content)
                st.write("Preview CMBulk File Locked Utrancell Script")
                with st.expander("Click to view script"):
                    st.code(text_file_content)
                st.download_button(
                    label="Download CMBulk Zipped Files",
                    data=zip_buffer_cmbulk,
                    file_name=f"RNC_Delete_Utrancell_{date_str}.zip",
                    mime="application/zip"
                )
                st.write("Preview CMEdit File Delete Utrancell Script")
                with st.expander("Click to view script"):
                    st.code(text_area_content)
                st.download_button(
                    label="Download CMEdit Zipped Files",
                    data=zip_buffer_cmedit,
                    file_name=f"RNC_Delete_Utrancell_{date_str}.zip",
                    mime="application/zip"
                )
            else:
                # If there's only 1 RNC, generate a single text file
                st.write("Preview CMBulk File Locked Utrancell Script")
                with st.expander("Click to view script"):
                    st.code("".join(text_file_content))
                filename_cmbulk = f"{rnc_list[0]}_Delete_Utrancell_CMBUlk_{date_str}.txt"
                st.download_button(
                    label="Download CMBulk Text File",
                    data="".join(text_file_content),
                    file_name=filename_cmbulk,
                    mime="text/plain"
                )
                st.write("Preview CMEdit File Delete Utrancell Script")
                with st.expander("Click to view script"):
                    st.code(text_area_content)
                filename_cmbulk = f"{rnc_list[0]}_Delete_Utrancell_CMEdit_{date_str}.txt"
                st.download_button(
                    label="Download CMEdit Text File",
                    data="".join(text_area_content),
                    file_name=filename_cmbulk,
                    mime="text/plain"
                )
        else:
            st.error("Sheet 'DEL_T-U21' not found in the uploaded file.")
    else:
        st.warning('⚠️ Please make sure you have sheet "DEL_T-U21" ⚠️')


if __name__ == "__main__":
    main()


