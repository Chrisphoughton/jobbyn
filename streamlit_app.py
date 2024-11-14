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
    initial_sidebar_state="expanded",
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
    SELECT DISTINCT mapped_role, rics_k50, metro_area, seniority FROM `jobbyn.jobbyn.jobs`
"""

# Use the cached function to get data
df_lookups = loading_lookups(lookups_query)
#make seniority a string
df_lookups["seniority"] = df_lookups["seniority"].astype(str)


st.title("Jobbyn")
st.caption("A job search tool for the Jobbyn Method. Please select search filters on sidebar.")
st.divider()

# Get unique list of metro_area and sort them
with st.sidebar:
    locations = df_lookups["metro_area"].unique()
    locations.sort()
    locationsAllFlag = st.checkbox("Select All Locations")
    if locationsAllFlag:
        locationOptions = locations
        st.multiselect("Select your Locations", locations,disabled=True,placeholder="All Locations Selected")
    else:
        locations = [loc.title() for loc in locations]
        locationOptions = st.multiselect("Select your Locations", locations)
        locationOptions = [loc.lower() for loc in locationOptions]
    st.divider()

    #filter industries based on selected locations
    df_lookups = df_lookups[df_lookups["metro_area"].isin(locationOptions)]
    industries = df_lookups["rics_k50"].unique()
    #remove null values
    industries = [industry for industry in industries if industry is not None]
    industries.sort()
    industriesAllFlag = st.checkbox("Select All Industries")
    if industriesAllFlag:
        industryOptions = industries
        st.multiselect("Select your Industries", industries,disabled=True,placeholder="All Industries Selected")
    else:
        industryOptions = st.multiselect("Select your Industries", industries)
    st.divider()

    #filter job families based on selected locations
    df_lookups = df_lookups[df_lookups["rics_k50"].isin(industryOptions)]
    jobFamilies = df_lookups["mapped_role"].unique()
    jobFamilies.sort()
    jobFamiliesAllFlag = st.checkbox("Select All Job Families")
    if jobFamiliesAllFlag:
        jobOptions = jobFamilies
        st.multiselect("Select your Job Families", jobFamilies,disabled=True,placeholder="All Job Families Selected")
    else:
        jobFamilies = [job.title() for job in jobFamilies]
        jobOptions = st.multiselect("Select your Job Families", jobFamilies)
        jobOptions = [job.lower() for job in jobOptions]
    st.divider()

    #filter seniority based on selected job families and locations
    df_lookups = df_lookups[df_lookups["mapped_role"].isin(jobOptions)]
    seniority = df_lookups["seniority"].unique()
    seniority.sort()
    seniorityAllFlag = st.checkbox("Select All Seniority Levels")
    if seniorityAllFlag:
        seniorityOptions = seniority
        st.multiselect("Select your Seniority Levels", seniority,disabled=True,placeholder="All Seniority Levels Selected")
    else:
        seniorityOptions = st.multiselect("Select your Seniority Levels", seniority)
    st.divider()

    formatted_location_options = ', '.join(f"'{loc}'" for loc in locationOptions) if len(locationOptions)>0 else "''"
    formatted_job_options = ', '.join(f"'{job}'" for job in jobOptions) if len(jobOptions)>0 else "''"
    formatted_seniority_options = ', '.join(f"'{seniority}'" for seniority in seniorityOptions) if len(seniorityOptions)>0 else "''"
    formatted_industry_options = ', '.join(f"'{industry}'" for industry in industryOptions) if len(industryOptions)>0 else "''"

    data_query = f"""
        SELECT * FROM `jobbyn.jobbyn.jobs`
        WHERE metro_area IN ({formatted_location_options}) AND mapped_role IN ({formatted_job_options}) AND seniority IN ({formatted_seniority_options}) AND rics_k50 IN ({formatted_industry_options})
    """

    searchButton = st.button("Search for Jobs",disabled=True if (len(locationOptions) == 0 or len(jobOptions) == 0 or len(seniorityOptions) == 0 or len(industryOptions) == 0 or len(df_lookups) > 100000) else False)
    #if either of the options are empty, return an empty dataframe
    if len(df_lookups) > 100000:
        st.caption("Too many options selected, please narrow your search")
    if len(locationOptions) == 0 or len(jobOptions) == 0 or len(seniorityOptions) == 0 or len(industryOptions) == 0:
        st.caption("Please select at least one option for each category")
    


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

