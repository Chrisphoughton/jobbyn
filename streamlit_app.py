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


st.title("Jobbyn")
st.subheader(
    "Please follow instructions to get the best job for you"
)
st.divider()

#read parquet file
df = pd.read_parquet("data/jobs.parquet")
#get list of job titles
jobFamilies = df["jobFamily"].unique()


jobOptions = st.multiselect(
    "Select your Job Families",
    jobFamilies,
)
locationOptions = st.multiselect(
    "Select your Locations",
    df["location"].unique(),
)

c1, c2 = st.columns([4, 1])
with c2:
    searchButton = st.button("Search for Jobs")
st.divider()
if searchButton:
    df_options = df[df["jobFamily"].isin(jobOptions) & df["location"].isin(locationOptions)]
    st.dataframe(df_options, use_container_width =True, hide_index=True)


