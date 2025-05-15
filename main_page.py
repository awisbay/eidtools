import streamlit as st

import streamlit as st
from PIL import Image

main_page = st.Page("homepage.py", title="Home", icon=":material/cable:")
create_utrancell = st.Page("create_utrancell.py", title="Utrancell Generator", icon=":material/cable:")
cr_generator = st.Page("cr_generator.py", title="CR Generator", icon=":material/api:")
baseband_change_cell = st.Page("baseband_change_cell.py", title="CR Cell Baseband/DUW", icon=":material/terrain:")

pg = st.navigation(
    {
        "Home" : [main_page],
        "3G MOCN" : [create_utrancell, cr_generator, baseband_change_cell],
    }
)
st.set_page_config(page_title="Eid Tools for ECT", page_icon="eric.png")
pg.run()