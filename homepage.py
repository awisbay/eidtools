import streamlit as st
from PIL import Image

im = Image.open("PIOT.jpg")
col1, col2, col3 = st.columns([1, 10, 1])

st.title("Welcome to EID Tools for ECT")
st.divider()

st.image(im, width=1000)
caption = "Ericsson Office in Indonesia"

st.divider()

cola, colb = st.columns(spec=2)
cola.write(
        f"Made with patience 🤗 and Love 💝"
    )
colb.markdown(
        "<p style='text-align: right;'>ewisbay @2025</p>",
        unsafe_allow_html=True,
    )