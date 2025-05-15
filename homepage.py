import streamlit as st
from PIL import Image

im = Image.open("PIOT.jpg")
col1, col2, col3 = st.columns([1, 10, 1])

st.title("Welcome to EID Tools for ECT")
st.divider()

st.image(im, width=1000)
caption = "Vodafone IX Tool By Yupana"