import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="Jobbyn",
    page_icon="🏢",
    layout="centered",
    initial_sidebar_state="collapsed",
    menu_items={
        'About': "# This is a header. This is an *extremely* cool app!"
        
    }
)

st.title("Test Streamlit App")
st.write(
    "Let's start building! For help and inspiration, head over to [docs.streamlit.io](https://docs.streamlit.io/)."
)
