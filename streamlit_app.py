import streamlit as st
import pandas as pd
import numpy as np
from google.cloud import bigquery
import altair as alt

# Initialize the BigQuery client with the service account
# service_account_info = "jobbyn-a159f5cec022.json"
# client = bigquery.Client.from_service_account_json(service_account_info)

# # Initialize the BigQuery client with the service account
service_account_info = st.secrets["gcp_service_account"]
client = bigquery.Client.from_service_account_info(service_account_info)

st.set_page_config(
    page_title="Jobbyn",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'About': "# This is a header. This is an *extremely* cool app!"
    }
)

#initialize session state
if "df_options" not in st.session_state:
    st.session_state.df_options = None

# Function to query BigQuery and cache the result
@st.cache_data
def loading_lookups(query):
    query_job = client.query(query)
    dataframe = query_job.result().to_dataframe()
    return dataframe

def loading_data(query):
    query_job = client.query(query)
    dataframe = query_job.result().to_dataframe()
    return dataframe

# Your SQL query
lookups_query = """
    SELECT DISTINCT mapped_role, rics_k50, metro_area FROM `jobbyn.jobbyn.jobs`
"""

# Use the cached function to get data
df_lookups = loading_lookups(lookups_query)

st.title("Jobbyn")
st.divider()

# Get unique list of metro_area and sort them
locations = df_lookups["metro_area"].unique()
locations.sort()
locations = [loc.title() for loc in locations]
locationOptions = st.multiselect("Select your Locations", locations)
locationOptions = [loc.lower() for loc in locationOptions]

# Filter the data based on the selected locations
df_lookups = df_lookups[df_lookups["metro_area"].isin(locationOptions)]
jobFamilies = df_lookups["mapped_role"].unique()
jobFamilies.sort()
jobFamilies = [job.title() for job in jobFamilies]
jobOptions = st.multiselect("Select your Job Families", jobFamilies)
jobOptions = [job.lower() for job in jobOptions]

formatted_location_options = ', '.join(f"'{loc}'" for loc in locationOptions) if locationOptions else "''"
formatted_job_options = ', '.join(f"'{job}'" for job in jobOptions) if jobOptions else "''"

data_query = f"""
    SELECT * FROM `jobbyn.jobbyn.jobs`
    WHERE metro_area IN ({formatted_location_options}) AND mapped_role IN ({formatted_job_options})
"""

c1, c2 = st.columns([1, 5])
with c1:
    searchButton = st.button("Search for Jobs")

st.divider()

if searchButton:
    df_options = loading_data(data_query)
    df_options = df_options
    st.session_state["df_options"] = df_options  # Store DataFrame in session state

if st.session_state["df_options"] is not None:
    
    df_options = st.session_state["df_options"]
    company_count = df_options.groupby("ultimate_parent_company_name").size().reset_index(name="Count")
    company_count.rename(columns={"ultimate_parent_company_name": "Company"}, inplace=True)

    chart = alt.Chart(company_count).mark_bar().encode(
        x=alt.X("Count:Q", title="Number of Jobs"),
        y=alt.Y("Company:N", title="Company", sort="-x"),
        tooltip=["Company", "Count"]
    )
    with st.expander("Company Count", expanded=False):
        st.altair_chart(chart, use_container_width=True)
    #get dataframe from session state

    event = st.dataframe(
        df_options,
        column_config={
            "jobtitle_raw": st.column_config.TextColumn("Job Title"),
            "mapped_role": st.column_config.TextColumn("Job Family"),
            "ultimate_parent_company_name": st.column_config.TextColumn("Company"),
            "metro_area": st.column_config.TextColumn("Metro Area"),
            "state": st.column_config.TextColumn("State"),
            "location": st.column_config.TextColumn("Location"),
            "rics_k50": st.column_config.TextColumn("Industry"),
            "seniority": st.column_config.TextColumn("Seniority"),
            "total_compensation": st.column_config.NumberColumn("Total Compensation"),
            "remote_type": st.column_config.TextColumn("Remote Type"),
            "post_date": st.column_config.TextColumn("Posted Date"),
            "job_id": st.column_config.TextColumn("Job ID"),
        },
        use_container_width=True,
        selection_mode="single-row",
        on_select="rerun",
        hide_index=True
    )
    if event["selection"]["rows"]:
        
        row = event["selection"]["rows"][0]
        #filter df_options based on the selected row
        if row is not None:
            st.divider()
            st.write(df_options[df_options.index == row]["jobtitle_raw"].values[0])
            selected_job_id = df_options[df_options.index == row]["job_id"].values[0]
            skills_query = f"""
                SELECT skill, mapped_skill, skill_k25, skill_k150, skill_k500, skill_k1000 FROM `jobbyn.jobbyn.skills`
                WHERE job_id = {selected_job_id}
            """
            skills = loading_data(skills_query)
            st.dataframe(
                skills,
                column_config={
                    "skill": st.column_config.TextColumn("Original Skill"),
                    "mapped_skill": st.column_config.TextColumn("Mapped Skill"),
                    "skill_k25": st.column_config.TextColumn("Skill Group 1"),
                    "skill_k150": st.column_config.TextColumn("Skill Group 2"),
                    "skill_k500": st.column_config.TextColumn("Skill Group 3"),
                    "skill_k1000": st.column_config.TextColumn("Skill Group 4"),
                },
                use_container_width=True,
                hide_index=True
            )
            st.link_button("Search for Job", #use job title, company and metro area to search for job
                           f"https://www.google.com/search?q={df_options[df_options.index == row]['jobtitle_raw'].values[0]} {df_options[df_options.index == row]['ultimate_parent_company_name'].values[0]} {df_options[df_options.index == row]['metro_area'].values[0]}")
    else:
        st.caption("Select a row to show skills")

