import streamlit as st

import streamlit as st
from PIL import Image

main_page = st.Page("homepage.py", title="Home", icon="🏡")
create_utrancell = st.Page("create_utrancell.py", title="Utrancell Generator", icon=":material/cable:")
cr_delete = st.Page("cr_delete_utrancellrelation.py", title="CR Delete", icon=":material/api:")
cr_create = st.Page("cr_create_utrancellrelation.py", title="CR Create", icon=":material/api:")
baseband_change_cell = st.Page("baseband_change_cell.py", title="CR Cell Baseband/DUW", icon=":material/terrain:")

pg = st.navigation(
    {
        "Home" : [main_page],
        "3G MOCN" : [create_utrancell, cr_create, cr_delete, baseband_change_cell],
    }
)
st.set_page_config(page_title="Eid Tools for ECT", page_icon="eric.png")
pg.run()